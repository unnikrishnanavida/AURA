export type FileType =
    | "folder"
    | "document"
    | "image"
    | "video"
    | "audio"
    | "code"
    | "archive";

export type FileStatus =
    | "synced"
    | "uploading"
    | "processing"
    | "failed";

export interface FileItem {

    id: string;

    name: string;

    type: FileType;

    status: FileStatus;

    size: string;

    owner: string;

    modifiedAt: string;

    favorite: boolean;

    shared: boolean;

    aiIndexed: boolean;

}

export interface StorageStatistics {

    totalFiles: number;

    totalStorage: string;

    usedStorage: string;

    aiIndexed: number;

}

export interface FileFilter {

    search: string;

    type: FileType | "All";

    status: FileStatus | "All";

}

export interface FilesProps {

    className?: string;

}