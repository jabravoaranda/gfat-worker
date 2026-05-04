# Run nc convert for specific day
{
  "task_name": "tasks.lidar.task_nc_convert",
  "args": ["ALHAMBRA", "2024-09-09"]
}

# Run quicklook for specific day
{
  "task_name": "tasks.lidar.task_quicklook",
  "args": ["alhambra", "1064fta", "0.0","30000000.0", "2024-09-09"]
}

# Run convert to scc nc for specific day
{
    "task_name": "tasks.lidar.task_convert_scc",
    "args": ["alhambra", "783", "11:30:00", "12:30:00", "20.0", "1013.25", "2024-09-09"]
}

# Run send to scc server for specific day and SCC_ID
{
    "task_name": "tasks.lidar.task_send_to_scc",
    "args": ["alhambra", "783", "2024-09-04"]
}

# Run download from scc server 
{
    "task_name": "tasks.lidar.task_download_from_scc",
    "args": ["alhambra", "783", "2024-09-02"]
}

# Run plot from scc server
{
    "task_name": "tasks.lidar.task_plot_scc",
    "args": ["alhambra", "783", "2024-09-02"]
}


