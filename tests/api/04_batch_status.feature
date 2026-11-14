Feature: Batch Spoilage Status Retrieval

  Background:
    * url baseUrl
    Given path '/login'
    And request { username: 'operator_alice', password: 'securepass123' }
    When method POST
    Then status 200
    * def authToken = response.access_token

  Scenario: Querying an unknown batch returns 404 Not Found
    Given path '/batches/NON-EXISTENT-BATCH/status'
    And header Authorization = 'Bearer ' + authToken
    When method GET
    Then status 404

  Scenario: Querying an existing batch returns accurate risk score and level
    # 1. Post initial reading
    Given path '/readings'
    And header Authorization = 'Bearer ' + authToken
    And request { batch_id: 'KARATE-STATUS-BATCH', produce_type: 'mango', temperature_c: 11.5, humidity_pct: 60.0, timestamp: '2026-11-14T08:00:00Z' }
    When method POST
    Then status 201

    # 2. Retrieve status
    Given path '/batches/KARATE-STATUS-BATCH/status'
    And header Authorization = 'Bearer ' + authToken
    When method GET
    Then status 200
    And match response.batch_id == 'KARATE-STATUS-BATCH'
    And match response.produce_type == 'mango'
    And match response.risk_score == 0.0
    And match response.risk_level == 'OK'
    And match response.readings_count == 1
