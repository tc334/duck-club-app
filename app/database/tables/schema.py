sequences = [
    'seq_birds_id',
    'seq_hunts_id',
    'seq_users_id',
    'seq_properties_id',
    'seq_ponds_id',
    'seq_groupings_id',
    'seq_harvest_id'
]

enums = [
    {
        "name": "bird_type",
        "values": ('duck', 'goose', 'crane', 'other')
    },
    {
        "name": "hunt_status",
        "values": ('signup_open', 'signup_closed', 'draw_complete', 'hunt_open', 'hunt_closed')
    },
    {
        "name": "user_level",
        "values": ('administrator', 'owner', 'manager', 'member')
    },
    {
        "name": "user_status",
        "values": ('active', 'inactive')
    },
    {
        "name": "property_region",
        "values": ('Northern', 'Southern')
    },
    {
        "name": "pond_status",
        "values": ('open', 'closed')
    },
    {
        "name": "group_slot_type",
        "values": ('open', 'member', 'guest', 'invitation')
    }
]

schema = {
    "birds": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_birds_id') PRIMARY KEY"
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'extra': 'UNIQUE NOT NULL'
        },
        {
            'name': 'type',
            'type': 'enum_bird_type',
            'extra': ''
        },
    ],

    "hunts": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_hunts_id') PRIMARY KEY"
        },
        {
            'name': 'status',
            'type': 'enum_hunt_status',
            'extra': "NOT NULL DEFAULT 'signup_open'"
        },
        {
            'name': 'hunt_date',
            'type': 'DATE',
            'extra': 'UNIQUE NOT NULL'
        },
        {
            'name': 'signup_closed_auto',
            'type': 'BOOLEAN',
            'extra': 'NOT NULL'
        },
        {
            'name': 'signup_closed_time',
            'type': 'TIME(0)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'draw_method_auto',
            'type': 'BOOLEAN',
            'extra': 'DEFAULT FALSE'
        },
        {
            'name': 'hunt_open_auto',
            'type': 'BOOLEAN',
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_open_time',
            'type': 'TIME(0)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_close_auto',
            'type': 'BOOLEAN',
            'extra': 'NOT NULL'
        },
        {
            'name': 'hunt_close_time',
            'type': 'TIME(0)',
            'extra': 'NOT NULL'
        }
    ],

    "users": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_users_id') PRIMARY KEY"
        },
        {
            'name': 'public_id',
            'type': 'CHAR(36)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'first_name',
            'type': 'VARCHAR(30)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'last_name',
            'type': 'VARCHAR(30)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'email',
            'type': 'VARCHAR(30)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'password_hash',
            'type': 'CHAR(88)',
            'extra': "NOT NULL"
        },
        {
            'name': 'level',
            'type': 'enum_user_level',
            'extra': "DEFAULT 'member'"
        },
        {
            'name': 'status',
            'type': 'enum_user_status',
            'extra': "DEFAULT 'active'"
        },
        {
            'name': 'outstanding_balance',
            'type': 'NUMERIC(8,2)',
            'extra': 'DEFAULT 0.00'
        }
    ],

    "properties": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_properties_id') PRIMARY KEY"
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'extra': 'NOT NULL'
        },
        {
            'name': 'region',
            'type': 'enum_property_region',
            'extra': ''
        }
    ],

    "ponds": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_ponds_id') PRIMARY KEY"
        },
        {
            'name': 'property_id',
            'type': 'INT',
            'extra': '',
            'foreign': 'properties(id)'
        },
        {
            'name': 'name',
            'type': 'VARCHAR(30)',
            'extra': 'UNIQUE NOT NULL'
        },
        {
            'name': 'status',
            'type': 'enum_pond_status',
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'selected',
            'type': 'BOOLEAN',
            'extra': 'DEFAULT FALSE'
        }
    ],

    "groupings": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_groupings_id') PRIMARY KEY"
        },
        {
            'name': 'hunt_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'hunts(id)'
        },
        {
            'name': 'pond_id',
            'type': 'INT',
            'extra': '',
            'foreign': 'ponds(id)'
        },
        {
            'name': 'slot1_type',
            'type': 'enum_group_slot_type',
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot2_type',
            'type': 'enum_group_slot_type',
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot3_type',
            'type': 'enum_group_slot_type',
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot4_type',
            'type': 'enum_group_slot_type',
            'extra': "DEFAULT 'open'"
        },
        {
            'name': 'slot1_id',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'slot2_id',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'slot3_id',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'slot4_id',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'harvest_update_time',
            'type': 'TIME(0)',
            'extra': "DEFAULT '00:00:00'"
        },
        {
            'name': 'num_hunters',
            'type': 'INT',
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'num_ducks',
            'type': 'INT',
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'num_non',
            'type': 'INT',
            'extra': 'DEFAULT 0'
        }
    ],

    "harvest": [
        {
            'name': 'id',
            'type': 'INT',
            'extra': "DEFAULT nextval('seq_harvest_id') PRIMARY KEY"
        },
        {
            'name': 'group_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'groupings(id)'
        },
        {
            'name': 'count',
            'type': 'INT',
            'extra': 'NOT NULL'
        },
        {
            'name': 'bird_id',
            'type': 'INT',
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
        'name': 'sec_idx_hunt_date',
        'table': 'hunts',
        'columns': ('hunt_date',)
    },
    {
        'name': 'sec_idx_bird_type',
        'table': 'birds',
        'columns': ('type',)
    },
    {
        'name': 'sec_idx_user_email',
        'table': 'users',
        'columns': ('email',)
    },
    {
        'name': 'sec_idx_ponds_property',
        'table': 'ponds',
        'columns': ('property_id',)
    },
    {
        'name': 'sec_idx_groupings_hunt',
        'table': 'groupings',
        'columns': ('hunt_id',)
    },
    {
        'name': 'sec_idx_groupings_pond',
        'table': 'groupings',
        'columns': ('pond_id',)
    },
    {
        'name': 'sec_idx_harvest_group',
        'table': 'harvest',
        'columns': ('group_id',)
    },
    {
        'name': 'sec_idx_harvest_bird',
        'table': 'harvest',
        'columns': ('bird_id',)
    },
)
