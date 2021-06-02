<script>
    import Slider from "@bulatdashiev/svelte-slider";

    export let selectedModel

    export let numIterations = [50];
    export let iterationRange = [10, 500];
    export let selectedResolution = [1024, 1024];
    export let resolutionRange = [200, 4000];

</script>

<h3>{numIterations} iterations</h3>
<Slider
    min={iterationRange[0]}
    max={iterationRange[1]}
    step="1"
    bind:value={numIterations}
/>

{#if selectedModel.value == "aphantasia"}
    <h3>
        Resolution of {selectedResolution[0]} x {selectedResolution[1]}
    </h3>
    <Slider
        bind:value={selectedResolution}
        min={resolutionRange[0]}
        max={resolutionRange[1]}
        range
        step="8"
        on:input={(e) => console.log()}
    />
{/if}

<style>

</style>