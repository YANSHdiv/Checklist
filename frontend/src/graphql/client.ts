import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client';

const uri = import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8000/graphql';

export const client = new ApolloClient({
  link: new HttpLink({
    uri,
  }),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          releases: {
            merge(_existing, incoming) {
              return incoming;
            },
          },
        },
      },
    },
  }),
});
