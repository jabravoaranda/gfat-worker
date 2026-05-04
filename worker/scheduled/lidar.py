from datetime import date

from celery.schedules import crontab

yesterday = date.today().replace(day=date.today().day - 1).strftime("%Y-%m-%d")

scheduled = {
    'scheduled_nc_convert': { # Convert ALHAMBRA raw data to netCDF
        'task': 'tasks.lidar.task_nc_convert',
        'schedule': crontab(hour='*/2', minute='0'),
        'args': ('ALHAMBRA',),
    },
    'scheduled_lidar_quicklook': { # Generate ALHAMBRA quicklook images
        'task': 'tasks.lidar.task_quicklook',
        'schedule': crontab(hour='*/2', minute='30'),
        'args': ('alhambra', '1064fta', '0.0','100000000.0'),
    },    
    'scheduled_convert_scc_0030': { # Convert SCC raw data from 00h30-01h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='2, 6, 18', minute='0'),
        'args': ('alhambra', 781, "00:30:00", "01:30:00"),
    },
    'scheduled_convert_scc_0130': { # Convert SCC raw data from 01h30-02h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='3, 6, 18', minute='0'),
        'args': ('alhambra', 781, "01:30:00", "02:30:00"),
    },
    'scheduled_convert_scc_0230': { # Convert SCC raw data from 02h30-03h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='4, 6, 18', minute='0'),
        'args': ('alhambra', 781, "02:30:00", "03:30:00"),
    },
    'scheduled_convert_scc_0330': { # Convert SCC raw data from 03h30-04h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='5, 6, 18', minute='0'),
        'args': ('alhambra', 781, "03:30:00", "04:30:00"),
    },
    'scheduled_convert_scc_0430': { # Convert SCC raw data from 04h30-05h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='6, 18', minute='0'),
        'args': ('alhambra', 781, "04:30:00", "05:30:00"),
    }, 
    'scheduled_convert_scc_0530': { # Convert SCC raw data from 05h30-06h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='7, 20', minute='0'),
        'args': ('alhambra', 783, "05:30:00", "06:30:00"),
    },  
    'scheduled_convert_scc_0630': { # Convert SCC raw data from 06h30-07h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='8, 20', minute='0'),
        'args': ('alhambra', 783, "06:30:00", "07:30:00"),
    },
    'scheduled_convert_scc_0730': { # Convert SCC raw data from 07h30-08h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='9, 20', minute='0'),
        'args': ('alhambra', 783, "07:30:00", "08:30:00"),
    },  
    'scheduled_convert_scc_0830': { # Convert SCC raw data from 08h30-09h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='10, 20', minute='0'),
        'args': ('alhambra', 783, "08:30:00", "09:30:00"),
    },
    'scheduled_convert_scc_0930': { # Convert SCC raw data from 09h30-10h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='11, 20, 23', minute='0'),
        'args': ('alhambra', 783, "09:30:00", "10:30:00"),
    },
    'scheduled_convert_scc_1030': { # Convert SCC raw data from 10h30-11h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='12, 20, 23', minute='0'),
        'args': ('alhambra', 783, "10:30:00", "11:30:00"),
    },
    'scheduled_convert_scc_1130': { # Convert SCC raw data from 11h30-12h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='13, 20, 23', minute='0'),
        'args': ('alhambra', 783, "11:30:00", "12:30:00"),
    },
    'scheduled_convert_scc_1230': { # Convert SCC raw data from 12h30-13h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='14, 20, 23', minute='0'),
        'args': ('alhambra', 783, "12:30:00", "13:30:00"),
    },
    'scheduled_convert_scc_1330': { # Convert SCC raw data from 13h30-14h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='15, 20, 23', minute='0'),
        'args': ('alhambra', 783, "13:30:00", "14:30:00"),
    },
    'scheduled_convert_scc_1430': { # Convert SCC raw data from 14h30-15h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='16, 20, 23', minute='0'),
        'args': ('alhambra', 783, "14:30:00", "15:30:00"),
    },
    'scheduled_convert_scc_1830': { # Convert SCC raw data from 18h30-19h30 to 783 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='20, 23', minute='0'),
        'args': ('alhambra', 783, "18:30:00", "19:30:00"),
    },

    'scheduled_convert_scc_2030': { # Convert SCC raw data from 20h30-21h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='0, 6, 12', minute='0'),
        'args': ('alhambra', 781, "20:30:00", "21:30:00", 20.0, 1013.25, yesterday),
    },
    'scheduled_convert_scc_2130': { # Convert SCC raw data from 21h30-22h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='0, 6, 12', minute='0'),
        'args': ('alhambra', 781, "21:30:00", "22:30:00", 20.0, 1013.25, yesterday),
    },
    'scheduled_convert_scc_2230': { # Convert SCC raw data from 22h30-23h30 to 781 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc',
        'schedule': crontab(hour='0, 6, 12', minute='0'),
        'args': ('alhambra', 781, "22:30:00", "23:30:00", 20.0, 1013.25, yesterday),
    },     

    'scheduled_send_to_scc_781': { # Send 781 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='*/2', minute='0'),
        'args': ('alhambra', 781, yesterday),
    },
    'scheduled_send_to_scc_783': { # Send 783 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='*/2', minute='0'),
        'args': ('alhambra', 783, yesterday),
    },

    'scheduled_send_to_scc_781': { # Send 781 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='1-23/2', minute='0'),
        'args': ('alhambra', 781),
    },
    'scheduled_send_to_scc_783': { # Send 783 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='1-23/2', minute='0'),
        'args': ('alhambra', 783),
    },    

    'scheduled_download_from_scc': { # Download SCC data
        'task': 'tasks.lidar.task_download_from_scc',
        'schedule': crontab(hour='*/2', minute='45'),
        'args': ('alhambra'),
    },

    'scheduled_download_from_scc': { # Download SCC data
        'task': 'tasks.lidar.task_download_from_scc',
        'schedule': crontab(hour='1-23/2', minute='45'),
        'args': ('alhambra',yesterday),
    },

    'scheduled_plot_scc_781': { # Plot SCC 781 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='*/2', minute='0'),
        'args': ('alhambra', 781, yesterday),
    },
    'scheduled_plot_scc_783': { # Plot SCC 783 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='*/2', minute='0'),
        'args': ('alhambra', 783, yesterday),
    },
    'scheduled_plot_scc_781': { # Plot SCC 781 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='1-23/2', minute='0'),
        'args': ('alhambra', 781),
    },
    'scheduled_plot_scc_783': { # Plot SCC 783 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='1-23/2', minute='0'),
        'args': ('alhambra', 783),
    },

    'scheduled_convert_scc_dp': { # Convert SCC DP raw data to 773 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc_dp',
        'schedule': crontab(hour='*/12', minute='0'),
        'args': ('alhambra', 773, yesterday),
    },
    'scheduled_convert_scc_dp': { # Convert SCC DP raw data to 773 scc-config netCDF
        'task': 'tasks.lidar.task_convert_scc_dp',
        'schedule': crontab(hour='*/12', minute='0'),
        'args': ('alhambra', 773),
    },       
    'scheduled_send_to_scc_773': { # Send 773 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='*/12', minute='15'),
        'args': ('alhambra', 773, yesterday),
    },
    'scheduled_send_to_scc_773': { # Send 773 scc-config netCDF to SCC
        'task': 'tasks.lidar.task_send_to_scc',
        'schedule': crontab(hour='*/12', minute='15'),
        'args': ('alhambra', 773),
    },
    'scheduled_plot_scc_773': { # Plot SCC 773 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='*/12', minute='30'),
        'args': ('alhambra', 773, yesterday),
    },  
    'scheduled_plot_scc_773': { # Plot SCC 773 data
        'task': 'tasks.lidar.task_plot_scc',
        'schedule': crontab(hour='*/12', minute='30'),
        'args': ('alhambra', 773),
    },
}