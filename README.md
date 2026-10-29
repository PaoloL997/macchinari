# Macchinari

Web portal to manage the shop-floor machines of Brembana & Rolle. Each
machine runs a small HTTP agent (e.g. on a Raspberry Pi reachable over
Tailscale); the portal talks to the agents and exposes their capabilities
to the users:

- **files**: list, upload and delete files on the machine.
- **status**: read the current state of the machine.

Users log in with their Windows domain credentials through
[brembana-auth](https://github.com/PaoloL997/brembana-auth).

## Layout

| Path            | Purpose                                                        |
| --------------- | -------------------------------------------------------------- |
| `config/`       | Django settings and root URLs.                                 |
| `core/`         | Plants, machines, operation log, agent client and machines API. |
| `capabilities/` | One Django app per capability (`files`, `status`).             |
| `frontend/`     | Login page and single-page portal (templates, CSS, JS).        |

## Setup

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env   # fill in the LDAP settings
uv run manage.py migrate
uv run manage.py runserver
```

Machines and plants are configured in the Django admin at `/admin/`.
The admin action "Aggiorna manifest dall'agente" reads the capabilities
a machine supports from its agent.

## Tests

```sh
uv run manage.py test
```
