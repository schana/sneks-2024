import * as React from "react";

import { Amplify } from "aws-amplify";
import { Authenticator } from "@aws-amplify/ui-react";

import App from "./App";

export default function Root() {
  React.useEffect(() => {
    fetch("aws-config.json")
      .then((response) => response.json())
      .then((responseJson) => {
        Amplify.configure(responseJson);
      })
      .catch((err) => console.log(err));
  }, []);

  return (
    <Authenticator.Provider>
      <App />
    </Authenticator.Provider>
  );
}
