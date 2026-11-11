-- WEEK detail for flagged people (CIQ weeks only): task, daily hours, first 120 chars of notes, sheet status.
-- :wk = WEEK Sunday, :projects = account project ids, :emails = flagged people's emails (lowercase, quoted).
select lower(u.email::text) as email, te.project_id::text as project_id, t.name as task,
       te.sunday_hours, te.monday_hours, te.tuesday_hours, te.wednesday_hours, te.thursday_hours,
       te.friday_hours, te.saturday_hours, left(coalesce(te.notes,''),120) as notes,
       ts.status, ts.submitted_at::text as submitted_at
from x_time_entry te left join x_timesheet ts on ts.id = te.timesheet_id
left join x_task t on t.id = te.task_id
join agent_visible_users u on u.id = coalesce(ts.owner_id, te.owner_id)
where te.week_start = date ':wk' and te.project_id::text in (:projects) and lower(u.email::text) in (:emails)
order by 1,2,3
