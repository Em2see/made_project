broker_url = "redis://redis_host:6379/0"
result_backend = "redis://redis_host:6379/0"

task_serializer = "json"
task_list = 'project.tasks'
result_serializer = "json"
accept_content = ["json"]
time_zone = 'Europe/Moscow'
enabel_utc = True