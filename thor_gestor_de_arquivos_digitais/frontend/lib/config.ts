export const config = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  appUrl: process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  keycloakUrl:
    process.env.NEXT_PUBLIC_KEYCLOAK_URL ?? "http://localhost:8081",
  keycloakRealm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "thor",
  keycloakClientId:
    process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "thor-api",
};

export function keycloakRealmUrl() {
  return `${config.keycloakUrl}/realms/${config.keycloakRealm}`;
}
