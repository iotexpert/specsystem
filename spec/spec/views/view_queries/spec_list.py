import datetime
from django.conf import settings
from rest_framework import serializers
from spec.models import Spec
from utils.raw_sql import RawSQLQuerySet


def getSpecListQuerySet(reqDict) -> RawSQLQuerySet:
    # MariaDB and SQL Server do not have a common way of building sublist queries.
    if settings.DATABASES['default']['ENGINE'] == "django.db.backends.mysql": # pragma nocover Can't test both database types in one run
        col_exp = """
        s.num num,
        s.ver ver,
        s.title title,
        s.doc_type_id doc_type,
        s.department_id department,
        s.keywords keywords,
        s.state state,
        u.username created_by,
        s.create_dt create_dt,
        s.mod_ts mod_ts,
        s.jira jira,
        s.anon_access anon_access,
        s.reason reason,
        s.approved_dt approved_dt,
        s.sunset_extended_dt,
        dt.sunset_interval,
        dt.sunset_warn,
        null sunset_dt,
        null sunset_warn_dt,
        s.location_id location,
        (select min(h.mod_ts) from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') first_submit_dt ,
        (select max(h.mod_ts) from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') last_submit_dt ,
        (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Reject') reject_cnt ,
        (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Admin Update') admin_upd_cnt,
        case when s.state = 'Signoff' then
                (      select group_concat(distinct concat(ss.role_id,':',au.username) order by ss.role_id, au.username separator ', ')
                        from spec_sig ss
                        inner join auth_user au on au.id = ss.signer_id
                        where ss.spec_id = s.id and ss.signed_dt is null)
        end missing_sigs ,
            (
                select json_arrayagg(distinct json_object("username", au.username))
                from user_watch uw
                inner join auth_user au on au.id = uw.user_id
                where uw.num = s.num
            ) as watched
        """
    else: # pragma nocover Can't test both database types in one run
        col_exp = """
        s.num num,
        s.ver ver,
        s.title title,
        s.doc_type_id doc_type,
        s.department_id department,
        s.keywords keywords,
        s.state state,
        u.username created_by,
        s.create_dt create_dt,
        s.mod_ts mod_ts,
        s.jira jira,
        s.anon_access anon_access,
        s.reason reason,
        s.approved_dt approved_dt,
        s.sunset_extended_dt,
        dt.sunset_interval,
        dt.sunset_warn,
        null sunset_dt,
        null sunset_warn_dt,
        s.location_id location,
        (select min(h.mod_ts) from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') first_submit_dt ,
        (select max(h.mod_ts) from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') last_submit_dt ,
        (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Reject') reject_cnt ,
        (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Admin Update') admin_upd_cnt,
        case when s.state = 'Signoff' then
              (      select string_agg(concat(ss.role_id,':',au.username), ', ') within group (order by ss.role_id, au.username)
                     from spec_sig ss
                     inner join auth_user au on au.id = ss.signer_id
                     where ss.spec_id = s.id and ss.signed_dt is null)
        end missing_sigs,
        (
            select distinct au.username
            from user_watch uw with (nolock)
            inner join auth_user au on au.id = uw.user_id
            where uw.num = s.num
            for json path
        ) as watched
        """

    from_exp = """
        from spec s
        left join auth_user u on u.id = s.created_by_id
        left join doc_type dt on dt.name = s.doc_type_id
        """

    # filter_conditions conditions that are not simply a match in a returned field
    # MariaDB and SQL Server do not have a common way of building sublist queries.
    if settings.DATABASES['default']['ENGINE'] == "django.db.backends.mysql": # pragma nocover Can't test both database types in one run
        filter_conditions = {
            'not_incl_obsolete': "s.state <> '{s}'",
            'past_warn_date': """
                case when s.state = '{s}' and dt.sunset_interval is not null and dt.sunset_warn is not null then
                    case when s.sunset_extended_dt is not null
                        then addtime(s.sunset_extended_dt, sec_to_time((dt.sunset_interval-dt.sunset_warn)/1000/1000))
                        else addtime(s.approved_dt, sec_to_time((dt.sunset_interval-dt.sunset_warn)/1000/1000))
                    end
                end < utc_timestamp() """,
        }
    else: # pragma nocover Can't test both database types in one run
        filter_conditions = {
            'not_incl_obsolete': "s.state <> '{s}'",
            'past_warn_date': """
                case when s.state = '{s}' and dt.sunset_interval is not null and dt.sunset_warn is not null then
                    case when s.sunset_extended_dt is not null
                        then dateadd(second, (dt.sunset_interval-dt.sunset_warn)/1000/1000, s.sunset_extended_dt) at time zone 'utc'
                        else dateadd(second, (dt.sunset_interval-dt.sunset_warn)/1000/1000, s.approved_dt) at time zone 'utc'
                    end
                end < GETUTCDATE()""",
        }


    rqs = RawSQLQuerySet(col_exp=col_exp, filter_conditions=filter_conditions, from_exp=from_exp,
                            orderby_exp='num', reqDict=reqDict)
    return rqs


class SpecListSerializer(serializers.Serializer):
    def to_representation(self, instance):
        instance['sunset_dt'] = None
        if instance['state'] == 'Active' and instance['sunset_interval']:
            instance['sunset_interval'] = datetime.timedelta(seconds=instance['sunset_interval']/1000/1000)
            if instance['sunset_extended_dt']:
                instance['sunset_dt'] =  instance['sunset_extended_dt'] + instance['sunset_interval']
            elif instance['approved_dt']:
                instance['sunset_dt'] = instance['approved_dt'] + instance['sunset_interval']

        instance['sunset_warn_dt'] =  None
        if instance['sunset_dt'] and instance['sunset_warn']:
            instance['sunset_warn'] = datetime.timedelta(seconds=instance['sunset_warn']/1000/1000)
            instance['sunset_warn_dt'] = instance['sunset_dt'] - instance['sunset_warn']

        instance['anon_access'] = bool(instance['anon_access'])
        if instance['create_dt']:
            instance['create_dt'] = instance['create_dt'].isoformat()
        instance['mod_ts'] = instance['mod_ts'].isoformat()
        if instance['approved_dt']:
            instance['approved_dt'] = instance['approved_dt'].isoformat()
        if instance['sunset_dt']:
            instance['sunset_dt'] = instance['sunset_dt'].isoformat()
        if instance['sunset_warn_dt']:
            instance['sunset_warn_dt'] = instance['sunset_warn_dt'].isoformat()

        del instance['sunset_interval']
        del instance['sunset_warn']

        # If the spec is Active but past the sunset date, make it Obsolete
        if instance['state'] == 'Active' and instance['sunset_dt'] is not None and instance['sunset_dt'] < datetime.datetime.utcnow().isoformat():
            spec = Spec.objects.get(num=instance['num'], ver=instance['ver'])
            spec.checkSunset()
            instance['state'] = 'Obsolete'
        return instance

