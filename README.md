# Simple Config Server

This project aims to be a simple, straightforward and easy to self-host configuration server, while adhering to common configuration practices and requirements.

# Features

### Multiple Source Options
Configurations can be loaded from a variety of sources:
* Local file system folder
* (WIP) Redis instance
* (WIP) Pulled from git

### Environment Support
Configurations support environments internally -
Each configuration can contain any number of environments (prod / test / development / ...), where each environment is merged _on top_ of the "default" section.


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

`default` - contains the default configuration that will be present in __every__ environment of the configuration. The configuration presented under the default key is merged with the specified shards, depending on which environment is requested.

`shards` - a list of `shard` entities.

In cases where a given path is presented both in the default mapping and in a shard's mapping, the shard takes precedence and **overrides** the default (lists and nested objects are merged).

When a given configuration path exists in more than a single shard, the last shard in order of definition will take precedence and override previous values (lists and nested objects are merged).

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

## 1. Docker

#### Run the a container with port 8080 exposed:
`docker run -d -p 8080:8080 ghcr.io/ddevmoe/simple_config_server:latest`

##### Example - running with a volume mounted configuration files folder
`docker run -d -p 8080:8080 -e 'SCS_LOCAL_CONFIG_FOLDER_PATH=/mnt/configs' -v '/path/to/configs:/mnt/configs' ghcr.io/ddevmoe/simple_config_server:latest`

## 2. Using Source

#### Clone this repository

`git clone https://github.com/ddevmoe/simple_config_server.git`

#### Optional - Create (and activate) a virtual python environment (optional)

`python -m venv venv`

#### Install dependencies

`pip install -r requirements.txt`

#### Run the server

`python app.py`


# Configuration

Configuring the server is done using environment variables. Variables relevant to the server are prefixed with `SCS` (**S**imple **C**onfig **S**erver).

Every configuration option can be used regardless of hosting strategy (container / source code).

`SCS_HTTP_PORT` - Port to be used by the web server (default - `8080`).

`SCS_LOCAL_CONFIG_FOLDER_PATH` - Path to a directory where configuration files exist (default - `./configs`)


# Security

The project does not provide authentication and / or authorization mechanisms as of now. This might be changed depending on adoption and demand.

Certificate management should be handled by the hosting entity, or applied using a reverse proxy / router.

# Feature Roadmap
- [x] Dockerize the application
- [x] Enable feature configurability using env vars
- [x] Healthcheck route
- [ ] Support yaml & toml file formats
- [ ] Support git & redis sources
- [ ] Cross configuration reference support
- [ ] Tests & Coverage
- [ ] Enhanced logging

# License

This project is open sourced under MIT license, see the [LICENSE](LICENSE) file for more details.
