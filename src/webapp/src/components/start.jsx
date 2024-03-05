import * as React from "react";
import ContentLayout from "@cloudscape-design/components/content-layout";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import Link from "@cloudscape-design/components/link";
import ExpandableSection from "@cloudscape-design/components/expandable-section";

import AuthGuard from "./authenticator";

export default function Start() {
  return (
    <AuthGuard>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Documentation and resources to begin your Snek's journey"
          >
            Getting started
          </Header>
        }
      >
        <Container>
          <h2>Where to begin</h2>
          <p>
            Follow the{" "}
            <Link href="/docs/index.html">getting started guide</Link> to start
            making your Snek. When your Snek is ready,{" "}
            <Link href="/submit">upload</Link> your <code>submission.py</code>{" "}
            to have it evaluated.
          </p>
          <h2>FAQ</h2>
          <ExpandableSection headerText="How do I run multiple sneks?">
            There are two options:
            <dl>
              <dt>1. Duplicate the behavior of your snek.</dt>
              <dd>
                In <code>src/scripts/__init__.py</code>, you can add a line to
                run multiple instances of your Snek at a time. The line should
                be added directly above the <code>runner.main()</code> line:
                <pre>
                  <code>sneks_config.registrar_submission_sneks = 10</code>
                </pre>
              </dd>
              <dt>
                2. Add additional Sneks with different behavior. Note: this will
                make the local validation fail, since it is checking that only
                one Snek exists.
              </dt>
              <dd>
                <ol>
                  <li>
                    Create a folder within the <code>submission</code> folder
                    for the additional snek.
                  </li>
                  <li>
                    Copy the <code>__init__.py</code> and{" "}
                    <code>submission.py</code> from the <code>submission</code>{" "}
                    folder into the new folder.
                  </li>
                </ol>
              </dd>
            </dl>
          </ExpandableSection>
          <ExpandableSection headerText="What if my question isn't here?">
            Reach out to your contest coordinator or{" "}
            <Link external href="mailto:admin@sneks.dev">
              email the admin
            </Link>
            .
          </ExpandableSection>
        </Container>
      </ContentLayout>
    </AuthGuard>
  );
}
