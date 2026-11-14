Feature: Produce Sensor Readings Telemetry Ingest

  Background:
    * url baseUrl
    Given path '/login'
    And request { username: 'operator_alice', password: 'securepass123' }
    When method POST
    Then status 200
    * def authToken = response.access_token

  Scenario: Ingest valid sensor reading within safe range
    * def nowIso = '2026-11-14T10:00:00Z'
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-01', produce_type: 'tomato', temperature_c: 12.5, humidity_pct: 65.0, timestamp: nowIso }
    When method POST
    Then status 201
    And match response.status == 'accepted'
    And match response.batch_id == 'KARATE-BATCH-01'
    And match response.risk_level == 'OK'

  Scenario: Ingest sensor reading with out-of-range sensor temperature returns 422
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-01', produce_type: 'tomato', temperature_c: 85.0, humidity_pct: 65.0, timestamp: '2026-11-14T10:05:00Z' }
    When method POST
    Then status 422

  Scenario: Ingest sensor reading with future timestamp returns 422
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-01', produce_type: 'tomato', temperature_c: 12.0, humidity_pct: 65.0, timestamp: '2099-01-01T00:00:00Z' }
    When method POST
    Then status 422

  Scenario: Ingest sensor reading with wrong type returns 400 Bad Request
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-01', produce_type: 'tomato', temperature_c: 'extreme_heat', humidity_pct: 65.0, timestamp: '2026-11-14T10:05:00Z' }
    When method POST
    Then status 400

  Scenario: Duplicate reading for same batch and timestamp is ignored with 200 OK
    * def fixedTs = '2026-11-14T09:30:00Z'
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-DUP', produce_type: 'tomato', temperature_c: 12.0, humidity_pct: 50.0, timestamp: fixedTs }
    When method POST
    Then status 201

    # Second submission with identical timestamp
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-BATCH-DUP', produce_type: 'tomato', temperature_c: 12.0, humidity_pct: 50.0, timestamp: fixedTs }
    When method POST
    Then status 200
    And match response.status == 'ignored'
