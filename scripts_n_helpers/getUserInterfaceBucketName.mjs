#!/usr/bin/node

import { readFile } from 'fs/promises';

let outputs = JSON.parse(await readFile("./outputs.json", "utf8"));

for (const [key, value] of Object.entries(outputs)) {
    if (key.includes("-backend-")) {
        // backend
        // do nothing
    } else if (key.includes("-")) {
        // main
        for (const [innerKey, innerValue] of Object.entries(value)) {
            if (innerKey.startsWith("WebsiteUserInterfaceBucketName")) {
                process.stdout.write(innerValue)
            }
        }    
    };
}


