import { useEffect, useRef } from 'react';

import type { EmployerDetail as EmployerDetailRecord } from '../api/employerContracts';
import { useLanguage } from '../i18n/LanguageProvider';

type EmployerDetailProps = {
  detail: EmployerDetailRecord | null;
  failureKind: 'validation' | 'not_found' | 'forbidden' | 'conflict' | 'unavailable' | 'unexpected' | null;
  isLoading: boolean;
  autoFocus?: boolean;
};

export function EmployerDetail({ detail, failureKind, isLoading, autoFocus = true }: EmployerDetailProps) {
  const { messages } = useLanguage();
  const detailHeadingRef = useRef<HTMLHeadingElement>(null);
  const detailFailureHeadingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (autoFocus && detail !== null && !isLoading) {
      detailHeadingRef.current?.focus();
    }
  }, [autoFocus, detail, isLoading]);

  useEffect(() => {
    if (failureKind !== null && !isLoading) {
      detailFailureHeadingRef.current?.focus();
    }
  }, [failureKind, isLoading]);

  if (isLoading) {
    return (
      <section aria-label={messages.employerDetailLoadingHeading}>
        <h3>{messages.employerDetailLoadingHeading}</h3>
        <p role="status">{messages.employerDetailLoadingBody}</p>
      </section>
    );
  }

  if (detail === null) {
    if (failureKind === null) {
      return null;
    }

    const failureCopy =
      failureKind === 'validation'
        ? {
            heading: messages.employerDetailValidationHeading,
            body: messages.employerDetailValidationBody,
          }
        : failureKind === 'not_found'
          ? {
              heading: messages.employerDetailNotFoundHeading,
              body: messages.employerDetailNotFoundBody,
            }
          : failureKind === 'forbidden'
            ? {
                heading: messages.employerDetailForbiddenHeading,
                body: messages.employerDetailForbiddenBody,
              }
            : failureKind === 'conflict'
              ? {
                  heading: messages.employerDetailConflictHeading,
                  body: messages.employerDetailConflictBody,
                }
              : failureKind === 'unavailable'
                ? {
                    heading: messages.employerDetailUnavailableHeading,
                    body: messages.employerDetailUnavailableBody,
                  }
                : {
                    heading: messages.employerDetailUnexpectedHeading,
                    body: messages.employerDetailUnexpectedBody,
                  };

    return (
      <section aria-live="assertive">
        <h3 ref={detailFailureHeadingRef} tabIndex={-1}>
          {failureCopy.heading}
        </h3>
        <p>{failureCopy.body}</p>
      </section>
    );
  }

  return (
    <section aria-label={messages.employerDetailLoadingHeading}>
      <h3 ref={detailHeadingRef} tabIndex={-1}>
        {messages.employerDetailLoadingHeading}
      </h3>
      <dl>
        <div>
          <dt>{messages.employerDetailNameLabel}</dt>
          <dd>{detail.displayName}</dd>
        </div>
        <div>
          <dt>{messages.employerDetailTypeLabel}</dt>
          <dd>{detail.employerType === 'business' ? messages.employerTypeBusiness : messages.employerTypeHousehold}</dd>
        </div>
        <div>
          <dt>{messages.employerDetailLifecycleLabel}</dt>
          <dd>{messages.employerLifecycleDraft}</dd>
        </div>
        <div>
          <dt>{messages.employerDetailSourceLabel}</dt>
          <dd>{messages.employerSourceStaffEntry}</dd>
        </div>
      </dl>
    </section>
  );
}
