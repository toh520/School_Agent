package com.schoolagent.core.management;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.identity.UserRole;
import com.schoolagent.core.management.ManagementDtos.FieldError;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

class ManagementServiceTest {

  private ManagementRepository repository;
  private ResourceValidator validator;
  private CsvTableParser csvParser;
  private ManagementService service;
  private CurrentIdentity admin;

  @BeforeEach
  void setUp() {
    repository = mock(ManagementRepository.class);
    validator = mock(ResourceValidator.class);
    csvParser = mock(CsvTableParser.class);
    service = new ManagementService(repository, validator, csvParser);
    admin = new CurrentIdentity(UUID.randomUUID(), UUID.randomUUID(), UserRole.INFO_ADMIN);
  }

  @Test
  void createsValidatedResourceAndWritesOperationLog() {
    Map<String, Object> values = Map.of("code", "CANTEEN-01", "name", "第一食堂", "source", "后勤公示");
    ValidationResult valid = new ValidationResult(values, List.of(), 100);
    ManagedResource resource = resource(ResourceType.CANTEEN, values);
    when(validator.validate(eq(ResourceType.CANTEEN), any(), isNull(), eq(0))).thenReturn(valid);
    when(validator.validate(eq(ResourceType.CANTEEN), any(), any(), eq(0))).thenReturn(valid);
    when(repository.create(ResourceType.CANTEEN, values, admin.userId())).thenReturn(resource);

    var response = service.create(admin, ResourceType.CANTEEN, values, "request-1");

    assertThat(response.values().get("code")).isEqualTo("CANTEEN-01");
    verify(repository)
        .logOperation(
            admin.userId(),
            "CREATE",
            "CANTEEN",
            resource.id().toString(),
            "CANTEEN-01",
            "食堂已新增",
            "request-1");
  }

  @Test
  void refusesToDeactivateReferencedParent() {
    ManagedResource resource =
        resource(
            ResourceType.CANTEEN, Map.of("code", "CANTEEN-01", "name", "第一食堂", "source", "后勤公示"));
    when(repository.findById(ResourceType.CANTEEN, resource.id()))
        .thenReturn(Optional.of(resource));
    when(repository.hasActiveChildren(ResourceType.CANTEEN, "CANTEEN-01")).thenReturn(true);

    assertThatThrownBy(
            () -> service.deactivate(admin, ResourceType.CANTEEN, resource.id(), "request-2"))
        .isInstanceOf(BusinessException.class);
    verify(repository, never()).deactivate(any(), any(), any());
  }

  @Test
  void reportsDuplicateResourceCodeAsConflict() {
    Map<String, Object> values = Map.of("code", "CANTEEN-01", "name", "第一食堂");
    when(validator.validate(eq(ResourceType.CANTEEN), eq(values), isNull(), eq(0)))
        .thenReturn(new ValidationResult(values, List.of(new FieldError(0, "code", "编码已存在")), 100));

    assertThatThrownBy(() -> service.create(admin, ResourceType.CANTEEN, values, "request-dup"))
        .isInstanceOfSatisfying(
            BusinessException.class,
            exception -> {
              assertThat(exception.getErrorCode()).isEqualTo(ErrorCode.CONFLICT);
              assertThat(exception.getStatus()).isEqualTo(HttpStatus.CONFLICT);
            });
    verify(repository, never()).create(any(), any(), any());
  }

  @Test
  void preservesGeneratedKnowledgeCodeWhenEditingOnlyVisibleFields() {
    Map<String, Object> stored =
        Map.of(
            "code", "KNOW-ABC12345",
            "name", "旧标题",
            "source", "校园知识库管理");
    ManagedResource existing = resource(ResourceType.KNOWLEDGE, stored);
    Map<String, Object> visibleValues =
        Map.of("name", "新标题", "category", "办事指南", "body", "新的知识正文内容。");
    when(repository.findById(ResourceType.KNOWLEDGE, existing.id()))
        .thenReturn(Optional.of(existing));
    when(validator.validate(eq(ResourceType.KNOWLEDGE), any(), eq(existing.id()), eq(0)))
        .thenAnswer(invocation -> new ValidationResult(invocation.getArgument(1), List.of(), 100));
    when(repository.update(
            eq(ResourceType.KNOWLEDGE), eq(existing.id()), any(), eq(admin.userId())))
        .thenReturn(existing);

    service.update(
        admin, ResourceType.KNOWLEDGE, existing.id(), visibleValues, "request-knowledge");

    verify(repository)
        .update(
            eq(ResourceType.KNOWLEDGE),
            eq(existing.id()),
            argThat(
                values ->
                    "KNOW-ABC12345".equals(values.get("code"))
                        && "校园知识库管理".equals(values.get("source"))),
            eq(admin.userId()));
  }

  @Test
  void importValidationReturnsPhysicalRowErrorsWithoutWriting() {
    Map<String, String> row = Map.of("code", "BOOK-01", "name", "缺少作者");
    when(csvParser.parse(any())).thenReturn(List.of(row));
    when(validator.validate(eq(ResourceType.BOOK), eq(row), isNull(), eq(2)))
        .thenReturn(
            new ValidationResult(
                Map.of("code", "BOOK-01", "name", "缺少作者"),
                List.of(new FieldError(2, "authors", "作者为必填项")),
                50));

    var preview = service.validateImport(ResourceType.BOOK, "csv");

    assertThat(preview.committed()).isFalse();
    assertThat(preview.errors()).singleElement().extracting(FieldError::row).isEqualTo(2);
    verify(repository, never()).create(any(), any(), any());
  }

  @Test
  void administratorCannotDisableOwnAccount() {
    assertThatThrownBy(
            () -> service.updateAccountStatus(admin, admin.userId(), "DISABLED", "request-3"))
        .isInstanceOf(BusinessException.class);
    verify(repository, never()).updateAccountStatus(any(), any());
  }

  private ManagedResource resource(ResourceType type, Map<String, Object> values) {
    return new ManagedResource(
        UUID.randomUUID(),
        type,
        String.valueOf(values.get("code")),
        String.valueOf(values.get("name")),
        null,
        Map.of(),
        String.valueOf(values.get("source")),
        "ACTIVE",
        admin.userId(),
        admin.userId(),
        Instant.now(),
        Instant.now());
  }
}
