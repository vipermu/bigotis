<script>
  import { Router, Route } from "svelte-routing";
  import NavLink from "./components/NavLink.svelte";
  import Editor from "./routes/Editor.svelte";

  // Used for SSR. A falsy value is ignored by the Router.
  export let url = "";
</script>

<Router url="{url}">
  <nav>
    <!-- <NavLink to="/">Editor</NavLink> -->
  </nav>
  <div>
    <Route path="/" component="{Editor}" />
  </div>
</Router>
