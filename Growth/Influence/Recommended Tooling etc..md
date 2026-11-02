
## deployments
preferred:
modern deployment model with colocated terraform
cloudrun gcp
github + actions

some teams use:
flux + kubernetes

less used/phased out:
azure devops + pipelines

---

## frontend tech

preferred:
next.js
tailwind
gfs kinetic
shadcn

used:
create-react-app

---

## programming languages/tools

north star (aligns with our team and what others want to use)
typescript or go depending on use-case
nest.js in place of express and express-openapi-validator
jest *or* vitest

Most teams use:
typescript
express
express-openapi-validator
jest

Less used/phased out:
javascript
mocha + chai


---

## logging and observability

used everywhere:
- datadog (link-to-sidecar-pattern)
- winston

this probably wants to go with infra for now as there's nothing outside of this used

## local tooling

gold:
pnpm
biome

used by some but almost always a mess
eslint + prettier (the merge and split just fucking ruined the usability)