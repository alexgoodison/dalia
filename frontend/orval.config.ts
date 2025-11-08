// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore -- orval types resolve after installing dev dependencies
import { defineConfig } from "orval";

export default defineConfig({
  backend: {
    input: "./openapi.json",
    output: {
      mode: "single",
      target: "./lib/api/client.ts",
      schemas: "./lib/api/model",
      client: "react-query",
      override: {
        query: {
          useQuery: true,
          useMutation: true,
          useInfinite: false,
          options: {
            staleTime: 5_000,
          },
        },
      },
    },
  },
});
