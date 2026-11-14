Feature: API Security, Token Validation and Tampering

  Background:
    * url baseUrl

  Scenario: Request with completely missing Authorization header fails with 401
    Given path '/alerts'
    When method GET
    Then status 401
    And match response.detail contains 'Missing or invalid Authorization header'

  Scenario: Request with tampered JWT token signature fails with 401
    # Generate forged JWT with invalid signature
    * def tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiJ9.invalidsignature1234567890abcdef'
    Given path '/alerts'
    And header Authorization = 'Bearer ' + tamperedToken
    When method GET
    Then status 401
    And match response.detail contains 'Invalid token'

  Scenario: Request with expired token format fails with 401
    # Expired token sample
    * def expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTYwOTQ1OTIwMH0.fake_sig'
    Given path '/alerts'
    And header Authorization = 'Bearer ' + expiredToken
    When method GET
    Then status 401
