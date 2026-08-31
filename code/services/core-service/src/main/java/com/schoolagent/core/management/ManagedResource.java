package com.schoolagent.core.management;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/** Internal persistence model shared by whitelisted management resource tables. */
record ManagedResource(
    UUID id,
    ResourceType type,
    String code,
    String name,
    String parentCode,
    Map<String, Object> payload,
    String source,
    String status,
    UUID createdBy,
    UUID updatedBy,
    Instant createdAt,
    Instant updatedAt) {}
