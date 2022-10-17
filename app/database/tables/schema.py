sequences = [
    'seq_birds_id',
    'seq_hunts_id',
    'seq_users_id',
    'seq_properties_id',
    'seq_ponds_id',
    'seq_groupings_id'
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
        "name": "participant_type",
        "values": ('member', 'guest')
    },
    {
        "name": "guest_type",
        "values": ('family', 'friend')
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
            'extra': ''
        },
        {
            'name': 'signup_closed_job_id',
            'type': 'STRING',
            'extra': ''
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
            'extra': ''
        },
        {
            'name': 'hunt_open_job_id',
            'type': 'STRING',
            'extra': ''
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
        },
        {
            'name': 'hunt_close_job_id',
            'type': 'STRING',
            'extra': ''
        },
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
            'type': 'VARCHAR(64)',
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
            'extra': "NOT NULL DEFAULT 'member'"
        },
        {
            'name': 'status',
            'type': 'enum_user_status',
            'extra': "NOT NULL DEFAULT 'active'"
        },
        {
            'name': 'confirmed',
            'type': 'BOOLEAN',
            'extra': "NOT NULL DEFAULT false"
        },
        {
            'name': 'outstanding_balance',
            'type': 'NUMERIC(8,2)',
            'extra': 'DEFAULT 0.00'
        },
        {
            'name': 'registered_on',
            'type': 'TIMESTAMP',
            'extra': ''
        },
        {
            'name': 'confirmed_on',
            'type': 'TIMESTAMP',
            'extra': ''
        }
    ],

    "guests": [
        {
            'name': 'id',
            'type': 'UUID',
            'extra': "DEFAULT gen_random_uuid() PRIMARY KEY"
        },
        {
            'name': 'full_name',
            'type': 'STRING',
            'extra': 'NOT NULL'
        },
        {
            'name': 'type',
            'type': 'enum_guest_type',
            'extra': "NOT NULL"
        },
        {
            'name': 'user_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'users(id)'
        },
        {
            'name': 'timestamp',
            'type': 'TIMESTAMP',
            'extra': 'DEFAULT current_timestamp()'
        },
    ],

    "invitations": [
        {
            'name': 'id',
            'type': 'UUID',
            'extra': "DEFAULT gen_random_uuid() PRIMARY KEY"
        },
        {
            'name': 'inviter_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'users(id)'
        },
        {
            'name': 'invitee_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'users(id)'
        },
        {
            'name': 'hunt_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'hunts(id)'
        },
        {
            'name': 'active',
            'type': 'BOOLEAN',
            'extra': 'DEFAULT true',
        },
        {
            'name': 'cancellation_notes',
            'type': 'STRING',
            'extra': '',
        },
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

    "scouting_reports": [
        {
            'name': 'id',
            'type': 'UUID',
            'extra': "DEFAULT gen_random_uuid() PRIMARY KEY"
        },
        {
            'name': 'pond_id',
            'type': 'INT',
            'extra': '',
            'foreign': 'ponds(id)'
        },
        {
            'name': 'hunt_id',
            'type': 'INT',
            'extra': '',
            'foreign': 'hunts(id)'
        },
        {
            'name': 'count',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'notes',
            'type': 'STRING',
            'extra': ""
        },
        {
            'name': 'created_by',
            'type': 'INT',
            'extra': '',
            'foreign': 'users(id)'
        },
        {
            'name': 'timestamp',
            'type': 'TIMESTAMP',
            'extra': 'DEFAULT current_timestamp()'
        },

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
            'name': 'harvest_update_time',
            'type': 'TIME(0)',
            'extra': "DEFAULT '00:00:00'"
        },
        {
            'name': 'num_hunters',
            'type': 'INT',
            'extra': 'DEFAULT 1'
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
        },
        {
            'name': 'draw_chip_raw',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'draw_position',
            'type': 'INT',
            'extra': ''
        },
        {
            'name': 'draw_position_ratio',
            'type': 'FLOAT',
            'extra': ''
        },
    ],

    "participants": [
        {
            'name': 'id',
            'type': 'UUID',
            'extra': "DEFAULT gen_random_uuid() PRIMARY KEY"
        },
        {
            'name': 'type',
            'type': 'enum_participant_type',
            'extra': "NOT NULL"
        },
        {
            'name': 'grouping_id',
            'type': 'INT',
            'extra': 'NOT NULL',
            'foreign': 'groupings(id) ON DELETE CASCADE'
        },
        {
            'name': 'user_id',
            'type': 'INT',
            'extra': '',
            'foreign': 'users(id)'
        },
        {
            'name': 'guest_id',
            'type': 'UUID',
            'extra': '',
            'foreign': 'guests(id)'
        },
        {
            'name': 'b_dog',
            'type': 'BOOLEAN',
            'extra': 'DEFAULT false'
        },
        {
            'name': 'num_atv_seats',
            'type': 'INT',
            'extra': 'DEFAULT 0'
        },
        {
            'name': 'pond_preference',
            'type': 'STRING',
            'extra': ''
        },
        {
            'name': 'notes',
            'type': 'STRING',
            'extra': ''
        },
    ],

    "harvest": [
        {
            'name': 'id',
            'type': 'UUID',
            'extra': "DEFAULT gen_random_uuid() PRIMARY KEY"
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
    {
        'name': 'sec_idx_scouting_hunt',
        'table': 'scouting_reports',
        'columns': ('hunt_id',)
    },
    {
        'name': 'sec_idx_participant_user',
        'table': 'participants',
        'columns': ('user_id',)
    },
)
