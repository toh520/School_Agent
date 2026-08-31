package com.schoolagent.core.identity;

import com.schoolagent.core.config.AuthProperties;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.stereotype.Service;

/** Issues short-lived access JWTs and high-entropy opaque refresh tokens. */
@Service
public class TokenService {

  private final JwtEncoder jwtEncoder;
  private final AuthProperties properties;
  private final SecureRandom secureRandom = new SecureRandom();

  public TokenService(JwtEncoder jwtEncoder, AuthProperties properties) {
    this.jwtEncoder = jwtEncoder;
    this.properties = properties;
  }

  public AccessToken accessToken(UserAccount user, UUID sessionId) {
    Instant issuedAt = Instant.now();
    Instant expiresAt = issuedAt.plus(properties.getAccessTokenMinutes(), ChronoUnit.MINUTES);
    JwtClaimsSet claims =
        JwtClaimsSet.builder()
            .issuer("school-agent-core")
            .issuedAt(issuedAt)
            .expiresAt(expiresAt)
            .subject(user.id().toString())
            .claim("sid", sessionId.toString())
            .claim("role", user.role().name())
            .build();
    JwsHeader header = JwsHeader.with(MacAlgorithm.HS256).build();
    String value = jwtEncoder.encode(JwtEncoderParameters.from(header, claims)).getTokenValue();
    return new AccessToken(value, Duration.between(issuedAt, expiresAt).toSeconds());
  }

  public String newRefreshToken() {
    byte[] bytes = new byte[48];
    secureRandom.nextBytes(bytes);
    return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
  }

  public String hashRefreshToken(String token) {
    try {
      byte[] digest =
          MessageDigest.getInstance("SHA-256").digest(token.getBytes(StandardCharsets.UTF_8));
      return HexFormat.of().formatHex(digest);
    } catch (NoSuchAlgorithmException exception) {
      throw new IllegalStateException("SHA-256 is unavailable", exception);
    }
  }

  public Instant refreshExpiry() {
    return Instant.now().plus(properties.getRefreshTokenDays(), ChronoUnit.DAYS);
  }

  public record AccessToken(String value, long expiresIn) {}
}
