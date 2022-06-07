schema = {
    "birds": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'type',
            'type': 'ENUM',
            'enum': ('duck', 'goose', 'crane', 'other'),
            'extra': ''
        },
    ],

    "groupings": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'hunt_id',
            'type': 'INT',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'pond_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'slot1_type',
            'type': 'ENUM',
            'enum': ('open', 'member', 'guest', 'invitation'),
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot2_type',
            'type': 'ENUM',
            'enum': ('open', 'member', 'guest', 'invitation'),
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot3_type',
            'type': 'ENUM',
            'enum': ('open', 'member', 'guest', 'invitation'),
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot4_type',
            'type': 'ENUM',
            'enum': ('open', 'member', 'guest', 'invitation'),
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot1_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'slot2_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'slot3_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'slot4_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'pond_pref',
            'type': 'VARCHAR(255)',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'harvest_ave',
            'type': 'FLOAT',
            'enum': None,
            'extra': ''
        }
    ],

    "harvest": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'group_id',
            'type': 'INT',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'count',
            'type': 'INT',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'bird_id',
            'type': 'INT',
            'enum': None,
            'extra': 'NOT NULL'
        }
    ],

    "hunts": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'status',
            'type': 'ENUM',
            'enum': ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open', 'hunt_closed'),
            'extra': "NOT NULL DEFAULT 'signup_open'"
        },
        {
            'name': 'hunt_date',
            'type': 'DATE',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'default_pond_pref',
            'type': 'VARCHAR(255)',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'harvest_average',
            'type': 'FLOAT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'signup_closed_auto',
            'type': 'BOOLEAN',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'signup_closed_time',
            'type': 'TIME(0)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'draw_method_auto',
            'type': 'BOOLEAN',
            'enum': None,
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'hunt_open_auto',
            'type': 'BOOLEAN',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_open_time',
            'type': 'TIME(0)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_close_auto',
            'type': 'BOOLEAN',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_close_time',
            'type': 'TIME(0)',
            'enum': None,
            'extra': 'NOT NULL'
        }
    ],

    "properties": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'region',
            'type': 'ENUM',
            'enum': ('Northern', 'Southern'),
            'extra': ''
        }
    ],

    "ponds": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'property_id',
            'type': 'INT',
            'enum': None,
            'extra': ''
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'status',
            'type': 'ENUM',
            'enum': ('open', 'closed'),
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'selected',
            'type': 'BOOLEAN',
            'enum': None,
            'extra': 'DEFAULT 0'
        }
    ],

    "users": [
        {
            'name': 'id',
            'type': 'INT',
            'enum': None,
            'extra': 'AUTO_INCREMENT PRIMARY KEY'
        },
        {
            'name': 'public_id',
            'type': 'CHAR(36)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'first_name',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'last_name',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'email',
            'type': 'VARCHAR(30)',
            'enum': None,
            'extra': 'NOT NULL'
        },
        {
            'name': 'password_hash',
            'type': 'CHAR(88)',
            'enum': None,
            'extra': "NOT NULL"
        },
        {
            'name': 'level',
            'type': 'ENUM',
            'enum': ('administrator', 'owner', 'manager', 'member'),
            'extra': "DEFAULT 'member'"
        },
        {
            'name': 'status',
            'type': 'ENUM',
            'enum': ('active', 'inactive'),
            'extra': "DEFAULT 'active'"
        },
        {
            'name': 'outstanding_balance',
            'type': 'DECIMAL(10,2)',
            'enum': None,
            'extra': 'DEFAULT 0.00'
        }
    ]
}
