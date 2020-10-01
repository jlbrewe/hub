/* tslint:disable */
/* eslint-disable */

/**
 * Stencila Hub Typescript Client
 *
 * This file is auto generated by OpenAPI Generator. Do not edit manually.
 */
import { exists, mapValues } from '../runtime';
import {
    AccountList,
    AccountListFromJSON,
    AccountListFromJSONTyped,
    AccountListToJSON,
} from './';

/**
 * 
 * @export
 * @interface ProjectList
 */
export interface ProjectList {
    /**
     * 
     * @type {number}
     * @memberof ProjectList
     */
    readonly id?: number;
    /**
     * 
     * @type {AccountList}
     * @memberof ProjectList
     */
    account: AccountList;
    /**
     * The user who created the project.
     * @type {number}
     * @memberof ProjectList
     */
    creator?: number | null;
    /**
     * The time the project was created.
     * @type {Date}
     * @memberof ProjectList
     */
    readonly created?: Date;
    /**
     * Name of the project. Lowercase only and unique for the account. Will be used in URLS e.g. https://hub.stenci.la/awesome-org/great-project.
     * @type {string}
     * @memberof ProjectList
     */
    name: string;
    /**
     * Title of the project to display in its profile.
     * @type {string}
     * @memberof ProjectList
     */
    title?: string | null;
    /**
     * Brief description of the project.
     * @type {string}
     * @memberof ProjectList
     */
    description?: string | null;
    /**
     * Is the project temporary?
     * @type {boolean}
     * @memberof ProjectList
     */
    temporary?: boolean;
    /**
     * Is the project publicly visible?
     * @type {boolean}
     * @memberof ProjectList
     */
    _public?: boolean;
    /**
     * A unique, and very difficult to guess, key to access this project if it is not public.
     * @type {string}
     * @memberof ProjectList
     */
    key?: string;
    /**
     * Path of the main file of the project
     * @type {string}
     * @memberof ProjectList
     */
    main?: string | null;
    /**
     * The name of the theme to use as the default when generating content for this project.
     * @type {string}
     * @memberof ProjectList
     */
    theme?: ProjectListThemeEnum;
    /**
     * Content to inject into the <head> element of HTML served for this project.
     * @type {string}
     * @memberof ProjectList
     */
    extraHead?: string | null;
    /**
     * Content to inject at the top of the <body> element of HTML served for this project.
     * @type {string}
     * @memberof ProjectList
     */
    extraTop?: string | null;
    /**
     * Content to inject at the bottom of the <body> element of HTML served for this project.
     * @type {string}
     * @memberof ProjectList
     */
    extraBottom?: string | null;
    /**
     * Where to serve the content for this project from.
     * @type {string}
     * @memberof ProjectList
     */
    liveness?: ProjectListLivenessEnum;
    /**
     * If pinned, the snapshot to pin to, when serving content.
     * @type {string}
     * @memberof ProjectList
     */
    pinned?: string | null;
    /**
     * Role of the current user on the project (if any).
     * @type {string}
     * @memberof ProjectList
     */
    readonly role?: string;
}

export function ProjectListFromJSON(json: any): ProjectList {
    return ProjectListFromJSONTyped(json, false);
}

export function ProjectListFromJSONTyped(json: any, ignoreDiscriminator: boolean): ProjectList {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'id': !exists(json, 'id') ? undefined : json['id'],
        'account': AccountListFromJSON(json['account']),
        'creator': !exists(json, 'creator') ? undefined : json['creator'],
        'created': !exists(json, 'created') ? undefined : (new Date(json['created'])),
        'name': json['name'],
        'title': !exists(json, 'title') ? undefined : json['title'],
        'description': !exists(json, 'description') ? undefined : json['description'],
        'temporary': !exists(json, 'temporary') ? undefined : json['temporary'],
        '_public': !exists(json, 'public') ? undefined : json['public'],
        'key': !exists(json, 'key') ? undefined : json['key'],
        'main': !exists(json, 'main') ? undefined : json['main'],
        'theme': !exists(json, 'theme') ? undefined : json['theme'],
        'extraHead': !exists(json, 'extraHead') ? undefined : json['extraHead'],
        'extraTop': !exists(json, 'extraTop') ? undefined : json['extraTop'],
        'extraBottom': !exists(json, 'extraBottom') ? undefined : json['extraBottom'],
        'liveness': !exists(json, 'liveness') ? undefined : json['liveness'],
        'pinned': !exists(json, 'pinned') ? undefined : json['pinned'],
        'role': !exists(json, 'role') ? undefined : json['role'],
    };
}

export function ProjectListToJSON(value?: ProjectList | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'account': AccountListToJSON(value.account),
        'creator': value.creator,
        'name': value.name,
        'title': value.title,
        'description': value.description,
        'temporary': value.temporary,
        'public': value._public,
        'key': value.key,
        'main': value.main,
        'theme': value.theme,
        'extraHead': value.extraHead,
        'extraTop': value.extraTop,
        'extraBottom': value.extraBottom,
        'liveness': value.liveness,
        'pinned': value.pinned,
    };
}

/**
* @export
* @enum {string}
*/
export enum ProjectListThemeEnum {
    Bootstrap = 'bootstrap',
    Elife = 'elife',
    F1000 = 'f1000',
    Galleria = 'galleria',
    Giga = 'giga',
    Latex = 'latex',
    Nature = 'nature',
    Plos = 'plos',
    Rpng = 'rpng',
    Skeleton = 'skeleton',
    Stencila = 'stencila',
    Tufte = 'tufte',
    Wilmore = 'wilmore'
}
/**
* @export
* @enum {string}
*/
export enum ProjectListLivenessEnum {
    Live = 'live',
    Latest = 'latest',
    Pinned = 'pinned'
}


