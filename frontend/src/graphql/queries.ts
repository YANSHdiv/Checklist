import { gql } from '@apollo/client';

export const RELEASE_FIELDS = gql`
  fragment ReleaseFields on ReleaseType {
    id
    name
    dueDate
    additionalInfo
    completedSteps
    status
    createdAt
    updatedAt
  }
`;

export const GET_RELEASES = gql`
  ${RELEASE_FIELDS}
  query GetReleases {
    releases {
      ...ReleaseFields
    }
  }
`;

export const CREATE_RELEASE = gql`
  ${RELEASE_FIELDS}
  mutation CreateRelease($input: CreateReleaseInput!) {
    createRelease(input: $input) {
      ...ReleaseFields
    }
  }
`;

export const UPDATE_RELEASE = gql`
  ${RELEASE_FIELDS}
  mutation UpdateRelease($input: UpdateReleaseInput!) {
    updateRelease(input: $input) {
      ...ReleaseFields
    }
  }
`;

export const TOGGLE_STEP = gql`
  ${RELEASE_FIELDS}
  mutation ToggleStep($releaseId: UUID!, $stepId: Int!) {
    toggleStep(releaseId: $releaseId, stepId: $stepId) {
      ...ReleaseFields
    }
  }
`;

export const DELETE_RELEASE = gql`
  mutation DeleteRelease($id: UUID!) {
    deleteRelease(id: $id)
  }
`;
