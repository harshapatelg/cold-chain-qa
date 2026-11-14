Feature: Authentication and Token Lifecycle API Tests

  Background:
    * url baseUrl

  Scenario: Successful login with valid operator credentials returns JWT
    Given path '/login'
    And request { username: 'operator_alice', password: 'securepass123' }
    When method POST
    Then status 200
    And match response.token_type == 'bearer'
    And match response.access_token == '#string'

  Scenario: Successful login with valid manager credentials returns JWT
    Given path '/login'
    And request { username: 'manager_bob', password: 'coldchain2026' }
    When method POST
    Then status 200
    And match response.token_type == 'bearer'
    And match response.access_token == '#string'

  Scenario: Failed login with invalid password returns 401 Unauthorized
    Given path '/login'
    And request { username: 'operator_alice', password: 'wrongpassword' }
    When method POST
    Then status 401
    And match response.detail == 'Invalid username or password'

  Scenario: Failed login with non-existent user returns 401 Unauthorized
    Given path '/login'
    And request { username: 'unregistered_user', password: 'securepass123' }
    When method POST
    Then status 401
