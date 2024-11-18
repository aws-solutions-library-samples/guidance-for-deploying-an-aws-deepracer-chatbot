export interface BuildConfig
{
    readonly AwsAccountId: string;
    readonly AwsRegion: string;

    readonly BedrockRegion: string;

    readonly AppName: string;
    readonly Environment : string;
}