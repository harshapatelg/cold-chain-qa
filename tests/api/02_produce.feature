Feature: Produce Registration API Tests

  Background:
    * url baseUrl
    * def loginResponse = call read('01_auth.feature@name=Successful login with valid operator credentials returns JWT')
    # Alternatively authenticate directly
    Given path '/login'
    And request { username: 'operator_alice', password: 'securepass123' }
    When method POST
    Then status 200
    * def authToken = response.access_token

  Scenario: Register a new produce type with valid temperature bounds
    Given path '/produce'
    And header Authorization = 'Bearer ' + authToken
    And request { name: 'blueberry', min_temp_c: 0.5, max_temp_c: 2.5 }
    When method POST
    Then status 201
    And match response.name == 'blueberry'
    And match response.min_temp_c == 0.5
    And match response.max_temp_c == 2.5
    And match response.status == 'registered'

  Scenario: Registering produce without token returns 401 Unauthorized
    Given path '/produce'
    And request { name: 'grapes', min_temp_c: 1.0, max_temp_c: 4.0 }
    When method POST
    Then status 401

  Scenario: Registering produce with invalid inverted bounds (min > max) returns 422
    Given path '/produce'
    And header Authorization = 'Bearer ' + authToken
    And request { name: 'invalid_fruit', min_temp_c: 15.0, max_temp_c: 5.0 }
    When method POST
    Then status 422
