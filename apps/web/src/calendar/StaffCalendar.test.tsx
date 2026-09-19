import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { LanguageProvider } from '../i18n/LanguageProvider';
import { StaffCalendar } from './StaffCalendar';

function renderCalendar() {
  return render(
    <LanguageProvider>
      <StaffCalendar />
    </LanguageProvider>,
  );
}

function getDayButton(day: string, date: string, count: string) {
  const button = screen.getAllByRole('button').find((candidate) => {
    const text = candidate.textContent;
    return text.includes(day) && text.includes(date) && text.includes(count);
  });
  if (!button) throw new Error(`Day button was not rendered for ${day} ${date}.`);
  return button;
}

describe('StaffCalendar', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('adds and removes a personal calendar event from the selected day', async () => {
    const user = userEvent.setup();
    let view = renderCalendar();
    await user.click(getDayButton('Tue', 'Jan 28', '2'));
    const form = screen.getByRole('heading', { name: 'Add event' }).closest('form');
    if (!form) throw new Error('Add event form was not rendered.');
    const eventForm = within(form);

    await user.type(eventForm.getByLabelText('Title'), 'Prepare demo script');
    await user.clear(eventForm.getByLabelText('Time'));
    await user.type(eventForm.getByLabelText('Time'), '15:15');
    await user.selectOptions(eventForm.getByLabelText('Duration'), '60 min');
    await user.selectOptions(eventForm.getByLabelText('Calendar'), 'personal');
    await user.type(eventForm.getByLabelText('Assigned to'), 'Mariela Torres');
    await user.type(eventForm.getByLabelText('Details'), 'Stakeholder presentation prep');
    await user.click(eventForm.getByRole('button', { name: 'Save event' }));

    expect(screen.getAllByText('Prepare demo script')).toHaveLength(2);
    expect(screen.getAllByText('Stakeholder presentation prep').length).toBeGreaterThanOrEqual(1);
    expect(getDayButton('Tue', 'Jan 28', '3')).toBeInTheDocument();

    view.unmount();
    view = renderCalendar();
    await user.click(getDayButton('Tue', 'Jan 28', '3'));
    expect(screen.getAllByText('Prepare demo script')).toHaveLength(2);

    await user.click(screen.getByRole('button', { name: 'Edit event' }));
    const editForm = screen.getByRole('heading', { name: 'Edit event' }).closest('form');
    if (!editForm) throw new Error('Edit event form was not rendered.');
    const editableEventForm = within(editForm);
    await user.clear(editableEventForm.getByLabelText('Title'));
    await user.type(editableEventForm.getByLabelText('Title'), 'Finalize demo script');
    await user.click(editableEventForm.getByRole('button', { name: 'Update event' }));
    expect(screen.getByRole('status')).toHaveTextContent('Event updated');
    expect(screen.queryByText('Prepare demo script')).not.toBeInTheDocument();
    expect(screen.getAllByText('Finalize demo script')).toHaveLength(2);

    await user.click(screen.getByRole('button', { name: 'Remove event' }));
    expect(screen.getByRole('status')).toHaveTextContent('Event removed');
    expect(screen.queryByText('Finalize demo script')).not.toBeInTheDocument();
    expect(getDayButton('Tue', 'Jan 28', '2')).toBeInTheDocument();

    view.unmount();
    renderCalendar();
    await user.click(getDayButton('Tue', 'Jan 28', '2'));
    expect(screen.queryByText('Finalize demo script')).not.toBeInTheDocument();
  });

  it('requires company calendar permission before removing company events', async () => {
    const user = userEvent.setup();
    renderCalendar();
    const form = screen.getByRole('heading', { name: 'Add event' }).closest('form');
    if (!form) throw new Error('Add event form was not rendered.');
    const eventForm = within(form);

    await user.type(eventForm.getByLabelText('Title'), 'Company briefing');
    await user.selectOptions(eventForm.getByLabelText('Calendar'), 'company');
    await user.click(eventForm.getByRole('button', { name: 'Save event' }));

    expect(screen.getAllByText('Company briefing')).toHaveLength(2);
    const gatedButtons = screen.getAllByRole('button', { name: 'Company calendar permission required' });
    expect(gatedButtons).toHaveLength(2);
    expect(gatedButtons.every((button) => button.hasAttribute('disabled'))).toBe(true);
  });
});
