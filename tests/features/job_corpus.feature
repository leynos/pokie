Feature: Representative job corpus and decision register
  Pokie's first release must demonstrate filtering, capture validation, and
  aggregation jobs whose outcomes are specified before any interpreter exists.

  Scenario Outline: A representative job's reference reproduces its outcomes
    Given the repository job "<job>"
    When the job's reference implementation runs against every case
    Then every observed outcome matches its expected outcome

    Examples:
      | job                   |
      | validate-user-records |
