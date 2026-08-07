import { useEffect, useRef } from 'react';

import type { EmployerDetail as EmployerDetailRecord } from '../api/employerContracts';
import { useLanguage } from '../i18n/LanguageProvider';

type EmployerDetailProps = {
  detail: EmployerDetailRecord | null;
  failureKind: 'not_found' | 'forbidden' | 'unavailable' | null;
  isLoading: boolean;
};

export function EmployerDetail({ detail, failureKind, isLoading }: EmployerDetailProps) {
  const { messages } = useLanguage();
  const detailHeadingRef = useRef<HTMLHeadingElement>(null);
  const detailFailureHeadingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (detail !== null && !isLoading) {
      detailHeadingRef.current?.focus();
    }
  }, [detail, isLoading]);

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
      failureKind === 'not_found'
        ? {
            heading: messages.employerDetailNotFoundHeading,
            body: messages.employerDetailNotFoundBody,
          }
        : failureKind === 'forbidden'
          ? {
              heading: messages.employerDetailForbiddenHeading,
              body: messages.employerDetailForbiddenBody,
            }
          : {
              heading: messages.employerDetailUnavailableHeading,
              body: messages.employerDetailUnavailableBody,
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
