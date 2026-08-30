package com.schoolagent.core.health;

public record SystemHealth(
    String status,
    DependencyHealth coreService,
    DependencyHealth agentService,
    DependencyHealth database) {}
