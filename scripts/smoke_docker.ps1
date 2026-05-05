$ErrorActionPreference = "Stop"

$projectName = "gfat-worker-smoke"
$composeArgs = @("-p", $projectName, "-f", "docker-compose.test.yml")
$apiUrl = "http://localhost:18000"
$stackStarted = $false

function Invoke-DockerCompose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    docker compose @composeArgs @Args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Test-DockerDaemon {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is installed, but the Docker daemon is not reachable. Start Docker Desktop and retry."
    }
}

function Wait-Api {
    $deadline = (Get-Date).AddSeconds(90)
    do {
        try {
            return Invoke-RestMethod -Uri "$apiUrl/" -Method Get -TimeoutSec 3
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    throw "API did not become ready at $apiUrl"
}

try {
    Test-DockerDaemon
    Invoke-DockerCompose up --build -d
    $stackStarted = $true

    $root = Wait-Api
    if ($root.name -ne "API Worker") {
        throw "Unexpected API root response: $($root | ConvertTo-Json -Compress)"
    }

    $registered = Invoke-RestMethod -Uri "$apiUrl/registered_tasks" -Method Get -TimeoutSec 10
    if ($registered.tasks -notcontains "tasks.misc.test_sum") {
        throw "tasks.misc.test_sum is not registered"
    }

    $body = @{
        task_name = "tasks.misc.test_sum"
        args = @(5, 10)
    } | ConvertTo-Json

    $queued = Invoke-RestMethod `
        -Uri "$apiUrl/task_queue" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 10

    if (-not $queued.id) {
        throw "Task queue response did not include an id"
    }

    $deadline = (Get-Date).AddSeconds(60)
    do {
        $details = Invoke-RestMethod -Uri "$apiUrl/task_queue/$($queued.id)" -Method Get -TimeoutSec 10
        if ($details.state -eq "SUCCESS") {
            if ([double]$details.result -ne 15) {
                throw "Expected task result 15, got $($details.result)"
            }
            Write-Output "Docker smoke test passed: task $($queued.id) returned 15."
            exit 0
        }
        if ($details.state -eq "FAILURE") {
            throw "Task failed: $($details | ConvertTo-Json -Compress)"
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "Task $($queued.id) did not finish before timeout"
} finally {
    if ($stackStarted) {
        Invoke-DockerCompose down -v --remove-orphans
    }
}
