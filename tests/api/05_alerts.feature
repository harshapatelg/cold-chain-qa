Feature: Active Alerts Listing and Acknowledgment

  Background:
    * url baseUrl
    Given path '/login'
    And request { username: 'manager_bob', password: 'coldchain2026' }
    When method POST
    Then status 200
    * def authToken = response.access_token

  Scenario: Unauthenticated request to /alerts returns 401 Unauthorized
    Given path '/alerts'
    When method GET
    Then status 401

  Scenario: List alerts and acknowledge an active alert
    # 1. Trigger an alert by sending 2 readings 45 min apart with temperature outside safe range
    # Produce leafy_greens safe range is 0.0 to 4.0 C
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-ALERT-BATCH', produce_type: 'leafy_greens', temperature_c: 2.0, humidity_pct: 80.0, timestamp: '2026-11-14T07:00:00Z' }
    When method POST
    Then status 201

    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-ALERT-BATCH', produce_type: 'leafy_greens', temperature_c: 15.0, humidity_pct: 80.0, timestamp: '2026-11-14T07:45:00Z' }
    When method POST
    Then status 201
    And match response.risk_level == 'WARNING'

    # 2. Query alerts list
    Given path '/alerts'
    And header Authorization = 'Bearer ' + authToken
    When method GET
    Then status 200
    And match response.alerts == '#[? _ >= 1]'
    * def firstAlert = response.alerts[0]
    * def alertId = firstAlert.alert_id

    # 3. Acknowledge the alert
    Given path '/alerts/' + alertId + '/ack'
    And header Authorization = 'Bearer ' + authToken
    When method POST
    Then status 200
    And match response.status == 'acknowledged'
    And match response.alert.status == 'ACKNOWLEDGED'

  Scenario: Acknowledging unknown alert returns 404 Not Found
    Given path '/alerts/ALT-99999-NOTFOUND/ack'
    And header Authorization = 'Bearer ' + authToken
    When method POST
    Then status 404
