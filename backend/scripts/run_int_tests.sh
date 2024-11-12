export API_HOST='http://app:5001'
export APP_SETTINGS='config.IntegrationTestConfig'

pytest tests/integration_tests/ -vv
