<script>
  import { Router, Route } from "svelte-routing";
  import Editor from "./routes/Editor.svelte";

  // Used for SSR. A falsy value is ignored by the Router.
  export let url = "";
</script>

<Router url="{url}">
  <nav>
  </nav>
  <div>
    <Route path="/" component="{Editor}" />
  </div>
</Router>
