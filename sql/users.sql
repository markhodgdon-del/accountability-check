-- Which roster emails have a CIQ user, and Mark's roles check is done separately with tenant.user.me.
select lower(email::text) as email, name from agent_visible_users where lower(email::text) in (:roster)
