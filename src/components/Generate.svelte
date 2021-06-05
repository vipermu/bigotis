<script>
    import { Jumper } from "svelte-loading-spinners";
    import {serverIP, apiPort} from "../utils.ts"
        
    export let generationParams
    export let generationResultDict
    
    let generatingImage = false;

    async function generate() {
        console.log("GENERATING WITH PARAMS", generationParams);
        generatingImage = true;

        const serverURL = `http://${serverIP}:${apiPort}`

        let fetchURL = new URL(`${serverURL}/generate`);
        fetchURL.search = new URLSearchParams(generationParams).toString();
        let jobId = undefined


        const getResults = async () => {
            if (typeof jobId == "undefined"){
                console.log("FETCHING DATA");
                const res = await fetch(fetchURL.toString(), {
                    method: "GET",
                });

                const jobResults = await res.json();
                console.log("JOB RESULTS", jobResults);
                jobId = jobResults.jobId
                
            } else {
                try {
                    console.log("FETCHING RESULTS")
                    let resultsURL = new URL(`${serverURL}/results/${jobId}`);
                    console.log("URL", resultsURL.toString())  

                    const results = await fetch(resultsURL.toString()).then(res => res.json())
                    
                    console.log("RESULTS ", results)

                    if (results.finished == "yup") {
                        console.log("DONE!");
                        generationResultDict = results
                        console.log("Generation result dict", generationResultDict);               
                        generatingImage = false;
                        clearInterval(interval)
                    } else {
                        console.log(results.finished);
                        // setTimeout(getResults, 0)

                    }
                } catch (err) {
                    // catches errors both in fetch and results.json
                    console.log("ERRROR")
                    console.log(err);
                }
            }
        };
        
        let interval = setInterval(getResults, 2000); 


    }
</script>

{#if !generatingImage}
    <div class="btn-container" style="margin-top: 20px">
        <button on:click={generate}>Generate</button>
    </div>
{:else}
    <div style="margin-top: 10px">
        <Jumper
            size="60"
            color="#BE3CC6"
            unit="px"
            duration="1.3s"
        />
    </div>
{/if}