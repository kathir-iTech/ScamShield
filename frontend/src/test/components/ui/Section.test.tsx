import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Section } from '@/components/ui/section';

describe('Section', () => {
  it('renders title and description', () => {
    render(<Section title="Details" description="More info">Content</Section>);
    expect(screen.getByText('Details')).toBeInTheDocument();
    expect(screen.getByText('More info')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders without title', () => {
    render(<Section>Content</Section>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders as section by default', () => {
    const { container } = render(<Section>Content</Section>);
    expect(container.querySelector('section')).toBeInTheDocument();
  });

  it('renders as div when as="div"', () => {
    const { container } = render(<Section as="div">Content</Section>);
    expect(container.querySelector('div')).toBeInTheDocument();
    expect(container.querySelector('section')).not.toBeInTheDocument();
  });
});
