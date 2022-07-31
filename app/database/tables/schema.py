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
            'extra': '',
            'foreign': 'properties(id)'
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
            'extra': 'NOT NULL',
            'foreign': 'hunts(id)'
        },
        {
            'name': 'pond_id',
            'type': 'INT',
            'enum': None,
            'extra': '',
            'foreign': 'ponds(id)'
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
            'name': 'harvest_update_time',
            'type': 'TIME(0)',
            'enum': None,
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'num_hunters',
            'type': 'INT',
            'enum': None,
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'harvest_ave_ducks',
            'type': 'FLOAT',
            'enum': None,
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'harvest_ave_non',
            'type': 'FLOAT',
            'enum': None,
            'extra': 'DEFAULT 0'
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
            'extra': 'NOT NULL',
            'foreign': 'groupings(id)'
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
            'extra': 'NOT NULL',
            'foreign': 'birds(id)'
        }
    ],
}

secondary_indices = (
    {
        'name': 'sec_idx_slot1',
        'table': 'groupings',
        'columns': ('slot1_type', 'slot1_id')
    },
    {
        'name': 'sec_idx_slot2',
        'table': 'groupings',
        'columns': ('slot2_type', 'slot2_id')
    },
    {
        'name': 'sec_idx_slot3',
        'table': 'groupings',
        'columns': ('slot3_type', 'slot3_id')
    },
    {
        'name': 'sec_idx_slot4',
        'table': 'groupings',
        'columns': ('slot4_type', 'slot4_id')
    },
    {
        'name': 'sec_idx_hunt_status',
        'table': 'hunts',
        'columns': ('status',)
    },
    {
        'name': 'sec_idx_bird_type',
        'table': 'birds',
        'columns': ('type',)
    },
)
