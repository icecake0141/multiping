## Supplement

### ASN Lookup Rate Limiting
To maintain the efficiency and reliability of ASN lookups, we implement rate limiting mechanisms to prevent abuse and overloading of resources. Each IP address is limited to X requests per minute, ensuring fair usage across all users.

### Efficiency Mechanisms
In addition to rate limiting, we utilize caching mechanisms to store previously fetched ASN data for a given IP address. This reduces the number of requests made to the upstream provider and speeds up the response time for subsequent lookups.