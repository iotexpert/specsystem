import datetime
import json
from rest_framework import serializers
from spec.models import Spec
from utils.raw_sql import RawSQLQuerySet


def getSpecListQuerySet(reqDict) -> RawSQLQuerySet:
    col_exp = """
       s.num num,
       s.ver ver,
       s.title title,
       s.doc_type_id doc_type,
       s.department_id department,
       s.keywords keywords,
       s.state state,
       u.username created_by,
       convert(varchar(50),s.create_dt at time zone 'utc', 127) create_dt,
       convert(varchar(50),s.mod_ts at time zone 'utc', 127) mod_ts,
       s.jira jira,
       s.anon_access anon_access,
       s.reason reason,
       convert(varchar(50),s.approved_dt at time zone 'utc', 127) approved_dt,
       s.sunset_extended_dt,
       case when s.state = 'Active' and dt.sunset_interval is not null then
              case when s.sunset_extended_dt is not null
                     then convert(varchar(50),dateadd(second, dt.sunset_interval/1000/1000, s.sunset_extended_dt) at time zone 'utc', 127)
                     else convert(varchar(50),dateadd(second, dt.sunset_interval/1000/1000, s.approved_dt) at time zone 'utc', 127)
              end
       end sunset_dt,
       case when s.state = 'Active' and dt.sunset_interval is not null and dt.sunset_warn is not null then
              case when s.sunset_extended_dt is not null
                     then convert(varchar(50),dateadd(second, (dt.sunset_interval-dt.sunset_warn)/1000/1000, s.sunset_extended_dt) at time zone 'utc', 127)
                     else convert(varchar(50),dateadd(second, (dt.sunset_interval-dt.sunset_warn)/1000/1000, s.approved_dt) at time zone 'utc', 127)
              end
       end sunset_warn_dt,
       s.location_id location,
       (select convert(varchar(50),min(h.mod_ts) at time zone 'utc', 127)  from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') first_submit_dt ,
       (select convert(varchar(50),max(h.mod_ts) at time zone 'utc', 127)  from spec_hist h where h.spec_id = s.id and h.change_type = 'Submit') last_submit_dt ,
       (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Reject') reject_cnt ,
       (select count(*) from spec_hist h where h.spec_id = s.id and h.change_type = 'Admin Update') admin_upd_cnt ,
       case when s.state = 'Signoff' then
              (      select string_agg(concat(ss.role_id,':',au.username), ', ')
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
        # If the spec is Active but past the sunset date, make it Obsolete
        if instance['state'] == 'Active' and instance['sunset_dt'] is not None and instance['sunset_dt'] < datetime.datetime.utcnow().isoformat():
            spec = Spec.objects.get(num=instance['num'], ver=instance['ver'])
            spec.checkSunset()
            instance['state'] = 'Obsolete'
        return instance

