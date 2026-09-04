package com.schoolagent.core.exam;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.exam.ExamDtos.ExamUpsertRequest;
import com.schoolagent.core.web.BusinessException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;

@ExtendWith(MockitoExtension.class)
class ExamServiceTest {
  @Mock private ExamRepository repository;
  private ExamService service;

  @BeforeEach
  void setUp() {
    service = new ExamService(repository);
  }

  @Test
  void createRejectsEndTimeThatIsNotAfterStartTime() {
    UUID userId = UUID.randomUUID();
    ExamUpsertRequest request = request(LocalTime.of(10, 0), LocalTime.of(9, 0));

    BusinessException error =
        assertThrows(BusinessException.class, () -> service.create(userId, request));

    assertEquals(HttpStatus.BAD_REQUEST, error.getStatus());
    verify(repository, never()).create(userId, request);
  }

  @Test
  void updateReturnsNotFoundWhenRecordDoesNotBelongToUser() {
    UUID userId = UUID.randomUUID();
    UUID examId = UUID.randomUUID();
    ExamUpsertRequest request = request(LocalTime.of(9, 0), LocalTime.of(11, 0));
    when(repository.update(userId, examId, request)).thenReturn(Optional.empty());

    BusinessException error =
        assertThrows(BusinessException.class, () -> service.update(userId, examId, request));

    assertEquals(HttpStatus.NOT_FOUND, error.getStatus());
  }

  @Test
  void createPersistsValidSchedule() {
    UUID userId = UUID.randomUUID();
    ExamUpsertRequest request = request(LocalTime.of(9, 0), LocalTime.of(11, 0));
    ExamResponse response =
        new ExamResponse(
            UUID.randomUUID(),
            request.subject(),
            request.examDate(),
            request.startTime(),
            request.endTime(),
            request.location(),
            Instant.now(),
            Instant.now());
    when(repository.create(userId, request)).thenReturn(response);

    assertEquals(response, service.create(userId, request));
  }

  private ExamUpsertRequest request(LocalTime start, LocalTime end) {
    return new ExamUpsertRequest("数据结构", LocalDate.of(2026, 9, 20), start, end, "教学楼 A201");
  }
}
