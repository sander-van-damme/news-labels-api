# news-labels-api
This is a simple API that clusters news articles and labels these clusters.

## Overview
The API creates [vector embeddings](https://platform.openai.com/docs/guides/embeddings) of the article contents and clusters these using [DBSCAN](https://en.wikipedia.org/wiki/DBSCAN).
The labels are then created with [GPT-3.5](https://platform.openai.com/docs/guides/text-generation).

## Request
Depending on the size of the request, you may need to increase the timeout of the request on the client side.

### Endpoint
- **URL**: `POST http://example.com/v1/create_labels/`

### Request Headers
- **Accept**: `application/json`
- **Content-Type**: `application/json`
- **X-Open-Ai-Api-Key**: `your-api-key`

### Request Body (JSON)
A list of news objects. Only the title properties is mandatory.
```json
[
  {
    "title": "string",
    "description": "string"
  }
]

```

### Response Body (JSON)
The description and label property are optional.
```json
{
  "title": "string",
  "description": "string",
  "label": "string"
}
```
