package com.schoolagent.core.identity;

import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/** Writes security audit events independently so denied operations cannot roll them back. */
@Service
public class AuditService {

  private final AuditRepository repository;

  public AuditService(AuditRepository repository) {
    this.repository = repository;
  }

  @Transactional(propagation = Propagation.REQUIRES_NEW)
  public void record(
      UUID userId,
      UUID actorUserId,
      String eventType,
      String module,
      String targetType,
      String targetId,
      String outcome,
      String requestId) {
    repository.record(
        userId, actorUserId, eventType, module, targetType, targetId, outcome, requestId);
  }
}
