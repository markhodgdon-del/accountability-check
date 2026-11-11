-- Accountability check: hours by person, Sunday week and project bucket. Read-only; run with tenant.query.sql.
-- :from = first TREND Sunday, :to = WEEK Sunday (both inclusive Sundays).
-- :projects = quoted, comma-separated CIQ project ids for the account (primary + context).
-- :roster   = quoted, comma-separated lowercase roster emails for the account.
-- Weeks from 2026-11-01 come from CIQ timesheets (x_time_entry / x_timesheet).
-- Earlier weeks come from ciq_time_entries_actuals, CIQ's synced copy of retired Harvest data,
-- bucketed by work_date (its week_start_date is a Monday: never use it). That copy has no notes.
-- Hours on projects outside the account are summed into project = 'other' (no names of other clients).
-- Never select bill or cost rates.
with ciq as (
  select coalesce(ts.owner_id, te.owner_id) as user_id, te.project_id::text as project_id, te.week_start as wk,
         coalesce(te.sunday_hours,0)+coalesce(te.monday_hours,0)+coalesce(te.tuesday_hours,0)
         +coalesce(te.wednesday_hours,0)+coalesce(te.thursday_hours,0)+coalesce(te.friday_hours,0)
         +coalesce(te.saturday_hours,0) as h,
         coalesce(te.notes,'') as notes, coalesce(ts.status,'none') as status
  from x_time_entry te left join x_timesheet ts on ts.id = te.timesheet_id
  where te.week_start between greatest(date ':from', date '2026-11-01') and date ':to'
), harv as (
  select ciq_user_id as user_id, ciq_project_id::text as project_id,
         (work_date - extract(dow from work_date)::int) as wk, hours as h, '' as notes, 'harvest' as status
  from ciq_time_entries_actuals
  where work_date between date ':from' and least(date ':to' + 6, date '2026-10-31')
), allrows as (select * from ciq union all select * from harv),
people as (
  select distinct user_id from allrows where project_id in (:projects)
  union select id from agent_visible_users where lower(email::text) in (:roster)
)
select lower(u.email::text) as email, u.name, a.wk::text as week,
       case when a.project_id in (:projects) then a.project_id else 'other' end as project,
       round(sum(a.h)::numeric,2) as hours,
       sum(case when a.status <> 'harvest' and btrim(a.notes) = '' and a.h >= 4 then 1 else 0 end) as blank_note_rows_ge4h,
       string_agg(distinct a.status, ',') as statuses
from allrows a join people p on p.user_id = a.user_id join agent_visible_users u on u.id = a.user_id
group by 1,2,3,4
order by 1,3,4
