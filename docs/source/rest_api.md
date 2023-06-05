# REST API

**Version:** v1

The REST API can be used to display published content from base Portfolio.

## Authentication

An access token is needed which has to be used as bearer authentication token in header of all requests.

**Header Format:** Authorization Bearer \<access_token>

```{note}
The access token can be created via management command: `python manage.py createapiuser <user_name>`
```

## User Data

### `GET /portfolio/api/v1/user/<uuid>/data/`

Fetch all published Portfolio entries of a user in which the user has any role.

#### Request

| Parameter       | Type   | Required | In     | Description                                                                        |
| --------------- | ------ | -------- | ------ | ---------------------------------------------------------------------------------- |
| Authorization   | Bearer | yes      | Header | Access Token                                                                       |
| Accept-Language | String | no       | Header | Defines the language of the response.<br><br>Allowed values: de, en<br>Default: en |
| UUID            | String | yes      | Path   | UUID of user                                                                       |

#### Response

**Content-Type:** application/json

##### Success

| Status | Description |
| ------ | ----------- |
| 200 OK |             |

| Parameter    | Type   | Description                                                           |
| ------------ | ------ | --------------------------------------------------------------------- |
| entry_labels | Object | Object containing localized labels of entries in format `key: label`. |
| data         | Array  | Array containing all results as objects.                              |

- label | String | Label of category.
- data | Array | Array containing the entries or subcategories with entries.

###### Examples

`GET /api/v1/user/7F4EF7F05E98435FAD27B40EC6DEEACC/data/`\
`Accept-Language: de`

```json
{
  "entry_labels": {
    "title": "Titel",
    "subtitle": "Untertitel",
    "type": "Typ",
    "role": "Rolle",
    "location": "Ort",
    "year": "Jahr"
  },
  "data": [
    {
      "label": "Dokumente/Publikationen",
      "data": [
        {
          "label": "Artikel",
          "data": [
            {
              "id": "7GhrxScV86mMXdn4Ar8scf",
              "title": "Ware Zukunft – Erzählung und Kommerzialisierung von Fortschrittsdenken im 19. Jh",
              "subtitle": null,
              "type": "Artikel",
              "role": "Autor*in",
              "location": "Wien (A)",
              "year": "2018"
            },
            {
              "id": "xJDGMw4FbenWP5zC9vwud7",
              "title": "Living Museum. Technikgeschichte im Zuhause",
              "subtitle": null,
              "type": "Artikel",
              "role": "Autor*in",
              "location": "Wien (A)",
              "year": "2017"
            }
          ]
        },
        {
          "label": "Beiträge in Sammelband",
          "data": [
            {
              "id": "ujiPmmPZCSeZAJbaMkA6hK",
              "title": "Futures & Options. Utopische Bildwelten des 19. Jahrhunderts am Beispiel der […]",
              "subtitle": null,
              "type": "Beitrag in Sammelband",
              "role": "Autor*in",
              "location": "Oberhausen (D)",
              "year": "2016"
            },
            {
              "id": "WGzpE46yrmYFNZL7CmMxtB",
              "title": "Right to the City! Right to the Museum!",
              "subtitle": null,
              "type": "Beitrag in Sammelband",
              "role": "Autor*in",
              "location": "Lissabon (P)",
              "year": "2015"
            }
          ]
        },
        {
          "label": "Sonstige Dokumente/Publikationen",
          "data": [
            {
              "id": "GJuNovNYkANJjr3d8xWdaS",
              "title": "Rezension zu Stefan Poser: Glücksmaschinen und Maschinenglück",
              "subtitle": null,
              "type": "wissenschaftliche Veröffentlichung",
              "role": "Autor*in",
              "location": "Baden-Baden (D)",
              "year": "2018"
            },
            {
              "id": "T3TL9FwjiTY7HEbogWqaDH"
              "title": "Sichtbarkeit, Sicherheit, Usability und Weiterverwendung – …",
              "subtitle": null,
              "type": "wissenschaftliche Veröffentlichung",
              "role": "Autor*in",
              "location": "Graz (A)",
              "year": "2018"
            }
          ]
        }
      ]
    },
    {
      "label": "Ausstellungen",
      "data": [
        {
          "id": "z99H3a6Ec7DEiKxoBiug2E",
          "title": "Tiefenrausch",
          "subtitle": null,
          "type": "Gruppenausstellung",
          "role": "Künstler*in",
          "location": "Linz (A)",
          "year": "2008"
        },
        {
          "id": "kB4sj2FmdqTNyqzkWpJzsN",
          "title": "3840 x 800 (gem. mit Julia Rosenberger)",
          "subtitle": null,
          "type": "Gruppenausstellung",
          "role": "Kurator*in",
          "location": null,
          "year": null
        }
      ]
    },
    {
      "label": "Konferenzen",
      "data": [
        {
          "id": "bqCMoxj7oMEjqoiDnLnpSW",
          "title": "Gastvortrag: Experimental Media Archaeology and the Politics of Kunstkopf […]",
          "subtitle": null,
          "type": "Gastvortrag",
          "role": "Organisation",
          "location": "Esch-sur-Alzette (L)",
          "year": "2017"
        },
        {
          "id": "zp2hCRAqUVMxNtugSLXaoE",
          "title": "Gewohnzimmert",
          "subtitle": "Interdisziplinäre / projektorientierte Lehrtätigkeit",
          "type": "Lehrtätigkeit",
          "role": "Vortragende*r",
          "location": null,
          "year": "2011"
        }
      ]
    },
    {
      "label": "Konferenzbeiträge",
      "data": [
        {
          "id": "8uFu3PzsLg7XHHUeQN2qJK",
          "title": "The Entanglement between Gesture, Media and Politics",
          "subtitle": null,
          "type": "Vortrag",
          "role": "Vortrag",
          "location": "Caputh (Berlin) (D)",
          "year": "2017"
        },
        {
          "id": "eMU8dCKn9tCwd46YK8nc7S",
          "title": "Living Museum. Technikgeschichte im Zuhause",
          "subtitle": null,
          "type": "Vortrag",
          "role": "Vortrag",
          "location": "Wien (A)",
          "year": "2016"
        }
      ]
    }
  ]
}
```

##### Error

| Status        | Description           |
| ------------- | --------------------- |
| 403 FORBIDDEN | Access token invalid. |
| 404 NOT FOUND | User not found.       |

## User Entry Data

### `GET /portfolio/api/v1/user/<uuid>/data/<entry_id>/`

Fetch detailed information for a specific entry of a user.

#### Request

| Parameter       | Type   | Required | In     | Description                                                                        |
| --------------- | ------ | -------- | ------ | ---------------------------------------------------------------------------------- |
| Authorization   | Bearer | yes      | Header | Access Token                                                                       |
| Accept-Language | String | no       | Header | Defines the language of the response.<br><br>Allowed values: de, en<br>Default: en |
| UUID            | String | yes      | Path   | UUID of user                                                                       |
| Entry ID        | String | yes      | Path   | ID of entry                                                                        |

#### Response

**Content-Type:** application/json

##### Success

| Status | Description |
| ------ | ----------- |
| 200 OK |             |

| Parameter   | Type         | Description                                                                                                               |
| ----------- | ------------ | ------------------------------------------------------------------------------------------------------------------------- |
| id          | String       | ID of entry                                                                                                               |
| data        | Array        | Array containing all data as objects.                                                                                     |
| - label     | String       | Label of data item.                                                                                                       |
| - value     | String/Array | String or Array containing the value/s of this data item.                                                                 |
| media       | Array        | Array containing all published media of this entry.                                                                       |
| - id        | String       | ID of media                                                                                                               |
| - type      | String\[1\]  | Type of media:<br>a … audio<br>d … document<br>i … image<br>v … video<br>x … other                                        |
| - original  | URL Path     | Path to originally uploaded file.                                                                                         |
| - published | Boolean      | Boolean indicating if media is published.                                                                                 |
| - license   | String       | License of media                                                                                                          |
| - mp3       | URL Path     | Path to mp3 (only for: audio)                                                                                             |
| - thumbnail | URL Path     | Path to thumbnail image (only for: document, image)                                                                       |
| - pdf       | URL Path     | Path to pdf (only for: document)                                                                                          |
| - previews  | Array        | Array containing different sizes for inclusion as responsive image (only for: image)                                      |
| - cover     | Object       | Object containing paths to video cover in two formats:<br>gif … animated gif<br>jpg … static jpg<br><br>(only for: video) |
| - playlist  | URL Path     | Path to hls m3u8 playlist (only for: video)                                                                               |
| relations   | Object       | Object with parents and children relations.                                                                               |
| - parents   | Array        | Array of parents containing objects with `id` and `title`.                                                                |
| - to        | Array        | Array of children containing objects with `id` and `title`.                                                               |

###### Examples

`GET /api/v1/user/7F4EF7F05E98435FAD27B40EC6DEEACC/data/7GhrxScV86mMXdn4Ar8scf/`\
`Accept-Language: de`

```json
{
  "id": "7GhrxScV86mMXdn4Ar8scf",
  "data": [
    {
      "label": "Titel",
      "value": "Ware Zukunft – Erzählung und Kommerzialisierung von Fortschrittsdenken im 19. Jh"
    },
    {
      "label": "Typ",
      "value": "Artikel"
    },
    {
      "label": "Schlagwörter",
      "value": ["Kulturgeschichte", "Kunstwissenschaften"]
    },
    {
      "label": "Texte",
      "value": [
        {
          "label": "Beschreibung",
          "value": "Große technische Visionen werden in der Politik, auf Ebene von Wirtschaftsunternehmen und nicht zuletzt in der Populärkultur verhandelt. So sorgt derzeit ein neuartiges Transportsystem für Furore, das 2012 vom Ingenieur und Unternehmer Elon Musk (1971–) präsentiert wurde. Musk schlägt mit dem „Hyperloop“ vor, Personen in luftleeren Röhren mit annähernder Schallgeschwindigkeit zu transportieren. Seither berichten Journalist/innen, Blogger und „Influencer“ in regelmäßigen Abständen über diese „Bahn der Zukunft“ . Fotorealistische Renderings sowie erste Teststrecken lassen die Öffentlichkeit das futuristische Transportmittel erfahren, ohne dass es für Passagiere bislang tatsächlich zugänglich wäre. \nMit Zukunftsentwürfen lässt sich Geld machen, dies gilt nicht nur für Ingenieure, sondern auch für die Populärkultur. Herausgeber/innen illustrierter Blätter und populärwissenschaftlicher Periodika griffen die technischen Visionen gerne auf, berichteten über die sensationellen Entwürfe, spitzten diese zu oder machten sich – wie im Falle der Karikatur – darüber lustig. Populäre Autor/innen ließen die Entwürfe in ihre Fortsetzungsromane einfließen und Spieleproduzent/innen verwendeten die technischen Visionen als Ausgangspunkt für die Entwicklung von Brettspielen. \nDer vorliegende Beitrag möchte den Fokus auf die kommerzielle Verwertung von „Vorauserwartungen“ (Radkau) legen. Er geht von der These aus, dass innerhalb eines transnationalen kulturellen Raums eine genreübergreifende Erzählung von technischen Zukünften in Populärkultur, Wirtschaft und Ingenieurswissenschaft vorausgesetzt werden muss, die als Grundlage für die Realisierung, d.h. Kapitalisierung, großer Infrastrukturprojekte dient. Die Erzählung schafft eine kollektiv geteilte und emotional aufgeladene Idee, die sich sowohl in der Populärkultur als auch von Ingenieuren kommerziell verwerten lassen. Dieser These geht der Beitrag anhand der Geschichte der pneumatischen Bahn sowie ihrer Erzählungen nach."
        }
      ]
    },
    {
      "label": "Autor*innen",
      "value": ["Florian Bettel"]
    },
    {
      "label": "Verlage",
      "value": ["Technisches Museum Wien"]
    },
    {
      "label": "Datum",
      "value": "2018-01-01"
    },
    {
      "label": "Ort",
      "value": ["Wien (A)"]
    },
    {
      "label": "URL",
      "value": "www.technischesmuseum.at/blaetter-fuer-technikgeschichte"
    },
    {
      "label": "erschienen in",
      "value": [
        [
          {
            "label": "Titel",
            "value": "Blätter für Technikgeschichte"
          }
        ]
      ]
    },
    {
      "label": "Band",
      "value": "80"
    },
    {
      "label": "Seiten",
      "value": "31–54"
    },
    {
      "label": "Ausgabe/Auflage",
      "value": "1000000"
    }
  ],
  "media": [
    {
      "id": "RJvd2dkVn8hdnbmxiVEuCo",
      "type": "i",
      "original": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/image_with_a_very_long_name_11111_dBS1ntv.jpg",
      "published": true,
      "license": "urheberrechtlich geschützt",
      "thumbnail": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/tn.jpg",
      "previews": [
        {
          "640w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-640.jpg"
        },
        {
          "768w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-768.jpg"
        },
        {
          "1024w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1024.jpg"
        },
        {
          "1366w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1366.jpg"
        },
        {
          "1600w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1600.jpg"
        },
        {
          "1920w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1920.jpg"
        }
      ],
      "response_code": 200
    }
  ],
  "relations": {
    "parents": [],
    "to": [
      {
        "id": "MX6iJcT33hom63Hn8ydFzj",
        "title": "Präsentation"
      }
    ]
  }
}
```

##### Error

| Status        | Description              |
| ------------- | ------------------------ |
| 403 FORBIDDEN | Access token invalid.    |
| 404 NOT FOUND | User or Entry not found. |

## Entry Data

### `GET /portfolio/api/v1/entry/<entry_id>/data/`

Fetch detailed information for a specific entry.

#### Request

| Parameter       | Type   | Required | In     | Description                                                                        |
| --------------- | ------ | -------- | ------ | ---------------------------------------------------------------------------------- |
| Authorization   | Bearer | yes      | Header | Access Token                                                                       |
| Accept-Language | String | no       | Header | Defines the language of the response.<br><br>Allowed values: de, en<br>Default: en |
| Entry ID        | String | yes      | Path   | ID of entry                                                                        |

#### Response

**Content-Type:** application/json

##### Success

| Status | Description |
| ------ | ----------- |
| 200 OK |             |

| Parameter   | Type         | Description                                                                                                               |
| ----------- | ------------ | ------------------------------------------------------------------------------------------------------------------------- |
| id          | String       | ID of entry                                                                                                               |
| data        | Array        | Array containing all data as objects.                                                                                     |
| - label     | String       | Label of data item.                                                                                                       |
| - value     | String/Array | String or Array containing the value/s of this data item.                                                                 |
| media       | Array        | Array containing all published media of this entry.                                                                       |
| - id        | String       | ID of media                                                                                                               |
| - type      | String\[1\]  | Type of media:<br>a … audio<br>d … document<br>i … image<br>v … video<br>x … other                                        |
| - original  | URL Path     | Path to originally uploaded file.                                                                                         |
| - published | Boolean      | Boolean indicating if media is published.                                                                                 |
| - license   | String       | License of media                                                                                                          |
| - mp3       | URL Path     | Path to mp3 (only for: audio)                                                                                             |
| - thumbnail | URL Path     | Path to thumbnail image (only for: document, image)                                                                       |
| - pdf       | URL Path     | Path to pdf (only for: document)                                                                                          |
| - previews  | Array        | Array containing different sizes for inclusion as responsive image (only for: image)                                      |
| - cover     | Object       | Object containing paths to video cover in two formats:<br>gif … animated gif<br>jpg … static jpg<br><br>(only for: video) |
| - playlist  | URL Path     | Path to hls m3u8 playlist (only for: video)                                                                               |
| relations   | Object       | Object with parents and children relations.                                                                               |
| - parents   | Array        | Array of parents containing objects with `id` and `title`.                                                                |
| - to        | Array        | Array of children containing objects with `id` and `title`.                                                               |

###### Examples

`GET /api/v1/entry/7GhrxScV86mMXdn4Ar8scf/data/`\
`Accept-Language: de`

```json
{
  "id": "7GhrxScV86mMXdn4Ar8scf",
  "data": [
    {
      "label": "Titel",
      "value": "Ware Zukunft – Erzählung und Kommerzialisierung von Fortschrittsdenken im 19. Jh"
    },
    {
      "label": "Typ",
      "value": "Artikel"
    },
    {
      "label": "Schlagwörter",
      "value": ["Kulturgeschichte", "Kunstwissenschaften"]
    },
    {
      "label": "Texte",
      "value": [
        {
          "label": "Beschreibung",
          "value": "Große technische Visionen werden in der Politik, auf Ebene von Wirtschaftsunternehmen und nicht zuletzt in der Populärkultur verhandelt. So sorgt derzeit ein neuartiges Transportsystem für Furore, das 2012 vom Ingenieur und Unternehmer Elon Musk (1971–) präsentiert wurde. Musk schlägt mit dem „Hyperloop“ vor, Personen in luftleeren Röhren mit annähernder Schallgeschwindigkeit zu transportieren. Seither berichten Journalist/innen, Blogger und „Influencer“ in regelmäßigen Abständen über diese „Bahn der Zukunft“ . Fotorealistische Renderings sowie erste Teststrecken lassen die Öffentlichkeit das futuristische Transportmittel erfahren, ohne dass es für Passagiere bislang tatsächlich zugänglich wäre. \nMit Zukunftsentwürfen lässt sich Geld machen, dies gilt nicht nur für Ingenieure, sondern auch für die Populärkultur. Herausgeber/innen illustrierter Blätter und populärwissenschaftlicher Periodika griffen die technischen Visionen gerne auf, berichteten über die sensationellen Entwürfe, spitzten diese zu oder machten sich – wie im Falle der Karikatur – darüber lustig. Populäre Autor/innen ließen die Entwürfe in ihre Fortsetzungsromane einfließen und Spieleproduzent/innen verwendeten die technischen Visionen als Ausgangspunkt für die Entwicklung von Brettspielen. \nDer vorliegende Beitrag möchte den Fokus auf die kommerzielle Verwertung von „Vorauserwartungen“ (Radkau) legen. Er geht von der These aus, dass innerhalb eines transnationalen kulturellen Raums eine genreübergreifende Erzählung von technischen Zukünften in Populärkultur, Wirtschaft und Ingenieurswissenschaft vorausgesetzt werden muss, die als Grundlage für die Realisierung, d.h. Kapitalisierung, großer Infrastrukturprojekte dient. Die Erzählung schafft eine kollektiv geteilte und emotional aufgeladene Idee, die sich sowohl in der Populärkultur als auch von Ingenieuren kommerziell verwerten lassen. Dieser These geht der Beitrag anhand der Geschichte der pneumatischen Bahn sowie ihrer Erzählungen nach."
        }
      ]
    },
    {
      "label": "Autor*innen",
      "value": ["Florian Bettel"]
    },
    {
      "label": "Verlage",
      "value": ["Technisches Museum Wien"]
    },
    {
      "label": "Datum",
      "value": "2018-01-01"
    },
    {
      "label": "Ort",
      "value": ["Wien (A)"]
    },
    {
      "label": "URL",
      "value": "www.technischesmuseum.at/blaetter-fuer-technikgeschichte"
    },
    {
      "label": "erschienen in",
      "value": [
        [
          {
            "label": "Titel",
            "value": "Blätter für Technikgeschichte"
          }
        ]
      ]
    },
    {
      "label": "Band",
      "value": "80"
    },
    {
      "label": "Seiten",
      "value": "31–54"
    },
    {
      "label": "Ausgabe/Auflage",
      "value": "1000000"
    }
  ],
  "media": [
    {
      "id": "RJvd2dkVn8hdnbmxiVEuCo",
      "type": "i",
      "original": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/image_with_a_very_long_name_11111_dBS1ntv.jpg",
      "published": true,
      "license": "urheberrechtlich geschützt",
      "thumbnail": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/tn.jpg",
      "previews": [
        {
          "640w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-640.jpg"
        },
        {
          "768w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-768.jpg"
        },
        {
          "1024w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1024.jpg"
        },
        {
          "1366w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1366.jpg"
        },
        {
          "1600w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1600.jpg"
        },
        {
          "1920w": "/p/vXMV5P60X0s0nO4VQy7LCrorW5ZGonurPpjWojP8UzJQPbKRO2CmdX/RJvd2dkVn8hdnbmxiVEuCo/preview-1920.jpg"
        }
      ],
      "response_code": 200
    }
  ],
  "relations": {
    "parents": [],
    "to": [
      {
        "id": "MX6iJcT33hom63Hn8ydFzj",
        "title": "Präsentation"
      }
    ]
  }
}
```

##### Error

| Status        | Description              |
| ------------- | ------------------------ |
| 403 FORBIDDEN | Access token invalid.    |
| 404 NOT FOUND | User or Entry not found. |

<style>
table {
  width:100%;
}
</style>
