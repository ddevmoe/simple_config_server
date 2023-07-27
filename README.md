# Simple Config Server

This projects aims at being a simple, straight forward and easy to self-host and maintain configuration server, while supporting common configuration practices and needs.

# Features

### Multiple Source Options
Configurations can be loaded from a variaety of sources:
* Local file system folder
* Redis instance
* Pulled from git

### Environment Support
Configurations support environments internally -
Each file can any number of environments (prod / test / development / ...), where each environment is merged _on top_ of the "default" section.

### (WIP) Inter-config References
Using a pre-defined syntax, one can refer values of one configuration file within another. This can come in handy when multiple files need to contain the same value (I.E. each service need to get the named of a shared SQL table).

# Configuration Structure & Basic Usage Example

Configuration entities consist of a top level object with two **mandatory** keys, and `shard` objects used to control specific environment values.

`shard`s are structured as follows (shown as JSON for this example):

```JSON
{
    "envs": ["prod", "test", "custom_env", "other_env"],
    "content": {
        "key1": "value1",
        "key2": 123
    }
}
```

The `envs` key contains a list of environment names, listing the environments that will include this shard.

The `content` key contains the configuration value of the shard.


The two mandatory keys of the top level object are - `default` and `shards`.

`default` - contains the default configuration that will be present in __every__ environment of the configuration. The configuration presented under the default key is merged with the specified shards, depending on which environment is requested. In cases where a value is presented both in the default mapping and in a shard's mapping - the shard takes precedence and **overrides** the default (lists and nested objects are still merged).

`shards` - a list of `shard` entities, where each one contains two keys

A complete configuration example (shown as JSON):

```JSON
{
    "default": {
        "SERVICE_NAME": "awesome_service",
        "DB": {
            "HOST": "localhost",
            "PORT": 9123,
            "RECREATE_TABLE": false
        }
    },
    "shards": [
        {
            "envs": ["prod"],
            "content": {
                "DB": {
                    "HOST": "production.db.host.domain",
                    "TABLE_NAME": "PROD_TABLE"
                }
            }
        },
        {
            "envs": ["dev"],
            "content": {
                "DB": {
                    "HOST": "dev.db.host.domain",
                    "TABLE_NAME": "DEV_TABLE"
                }
            }
        },
        {
            "envs": ["test"],
            "content": {
                "DB": {
                    "HOST": "test.db.host.domain",
                    "TABLE_NAME": "TEST_TABLE"
                }
            }
        },
        {
            "envs": ["dev", "test"],
            "content": {
                "DB": {
                    "RECREATE_TABLE": true
                }
            }
        }
    ]
}
```

Querying given configuration yields different result for each env:

`prod` -
```JSON
{
    "SERVICE_NAME": "awesome_service",
    "DB": {
        "HOST": "production.db.host.domain",
        "PORT": 9123,
        "RECREATE_TABLE": false,
        "TABLE_NAME": "PROD_TABLE"
    }
}
```

`dev` -
```JSON
{
    "SERVICE_NAME": "awesome_service",
    "DB": {
        "HOST": "dev.db.host.domain",
        "PORT": 9123,
        "RECREATE_TABLE": true,
        "TABLE_NAME": "DEV_TABLE"
    }
}
```

`test` -
```JSON
{
    "SERVICE_NAME": "awesome_service",
    "DB": {
        "HOST": "test.db.host.domain",
        "PORT": 9123,
        "RECREATE_TABLE": true,
        "TABLE_NAME": "TEST_TABLE"
    }
}
```

# Hosting Options

The project is intended to be selfhosted, using one of two options:

## (WIP) 1. Docker

#### Run the a container with port 8080 exposed:
`docker run -d -p 8080:8080 ddevmoe/simple_config_server:latest`

## 2. Using Source

#### Clone this repository

`git clone https://github.com/ddevmoe/simple_config_server.git`

#### Optional - Create (and activate) a virtual python environment (optional)

`python -m venv venv`

#### Install dependencies

`pip install -r requirements.txt`

#### Run the server

`python app.py`


# Security

The project does not provide authentication and / or authorization mechanisms as of now. This might be changed depending on adoption and demand.

Certificate management should be handled by the hosting entity, or applied using a reverse proxy / router.

# Feature Roadmap
- [ ] Cross configuration reference support
- [ ] Dockerize the application
- [ ] Support yaml & toml file formats
- [ ] Support git & redis sources
- [ ] Enable feature configurability using env vars
- [ ] Logging
- [ ] Tests & coverage
- [ ] Healthcheck / Sanity routes (?)

# License

This project is open sourced under MIT license, see the [LICENSE](LICENSE) file for more details.
