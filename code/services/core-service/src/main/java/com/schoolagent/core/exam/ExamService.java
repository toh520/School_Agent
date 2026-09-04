package com.schoolagent.core.exam;

import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.exam.ExamDtos.ExamUpsertRequest;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Enforces schedule rules independently of the model and scopes every mutation to its owner. */
@Service
class ExamService {
  private final ExamRepository repository;

  ExamService(ExamRepository repository) {
    this.repository = repository;
  }

  List<ExamResponse> list(UUID userId) {
    return repository.list(userId);
  }

  ExamResponse next(UUID userId) {
    return repository.next(userId).orElse(null);
  }

  @Transactional
  ExamResponse create(UUID userId, ExamUpsertRequest request) {
    validateTime(request);
    return repository.create(userId, request);
  }

  @Transactional
  ExamResponse update(UUID userId, UUID examId, ExamUpsertRequest request) {
    validateTime(request);
    return repository.update(userId, examId, request).orElseThrow(this::missing);
  }

  @Transactional
  void delete(UUID userId, UUID examId) {
    if (!repository.delete(userId, examId)) throw missing();
  }

  private void validateTime(ExamUpsertRequest request) {
    if (!request.endTime().isAfter(request.startTime())) {
      throw new BusinessException(ErrorCode.INVALID_REQUEST, HttpStatus.BAD_REQUEST);
    }
  }

  private BusinessException missing() {
    return new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND);
  }
}
